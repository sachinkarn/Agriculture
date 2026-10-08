"""Crop disease detection.

Flow: photo -> classifier (TorchScript model, trained by ml/train_disease.py) -> probabilities
over the classes of the crop the farmer selected -> disease, confidence, severity, actions.

If no trained model file exists the engine reports `ready == False` and the API answers 503.
We never fake a prediction and label it as a model result.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Protocol

import numpy as np
from PIL import Image

from . import knowledge
from .severity import lesion_percent, severity_label

_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)

_CROP_ALIASES = {"Corn_(maize)": "Corn", "Corn (maize)": "Corn", "Maize": "Corn"}
_DISEASE_NAMES = {
    "Cercospora_leaf_spot Gray_leaf_spot": "Gray leaf spot",
    "Haunglongbing_(Citrus_greening)": "Citrus greening",
}


class Predictor(Protocol):
    def predict(self, image: Image.Image) -> np.ndarray:
        """Return raw class scores (logits), one per label, in labels.json order."""


def preprocess(image: Image.Image, size: int = 224) -> np.ndarray:
    """Resize to size x size, scale to 0..1, normalise like ImageNet, shape (1, 3, H, W)."""
    arr = np.asarray(image.convert("RGB").resize((size, size), Image.BILINEAR), dtype=np.float32) / 255.0
    arr = (arr - _MEAN) / _STD
    return arr.transpose(2, 0, 1)[None, ...].astype(np.float32)


class TorchPredictor:
    """Runs a TorchScript model on CPU. Needs `torch` (see requirements-ml.txt)."""

    def __init__(self, path: Path):
        import torch  # imported lazily so the API still starts without torch installed

        self._torch = torch
        self._model = torch.jit.load(str(path), map_location="cpu")
        self._model.eval()

    def predict(self, image: Image.Image) -> np.ndarray:
        with self._torch.no_grad():
            out = self._model(self._torch.from_numpy(preprocess(image)))
        return out[0].cpu().numpy()


@dataclass
class LabelInfo:
    raw: str
    crop: str
    disease: str
    healthy: bool


def parse_label(raw: str) -> LabelInfo:
    """'Corn_(maize)___Northern_Leaf_Blight' -> crop 'Corn', disease 'Northern leaf blight'."""
    crop_raw, _, dis_raw = raw.partition("___")
    crop = _CROP_ALIASES.get(crop_raw, crop_raw.replace("_", " ").strip())
    healthy = dis_raw.strip().lower() == "healthy"
    if dis_raw in _DISEASE_NAMES:
        name = _DISEASE_NAMES[dis_raw]
    else:
        name = dis_raw.replace("_", " ").strip().lower().capitalize()
    return LabelInfo(raw=raw, crop=crop, disease="Healthy" if healthy else name, healthy=healthy)


def _softmax(x: np.ndarray) -> np.ndarray:
    e = np.exp(x - x.max())
    return e / e.sum()


@dataclass
class DiseaseResult:
    crop: str
    healthy: bool
    disease: str
    confidence: float
    severity: str
    severity_pct: float
    actions: list[str]
    uncertain: bool
    alternatives: list[dict] = field(default_factory=list)
    source: str = "model"

    def to_dict(self) -> dict:
        return asdict(self)


class DiseaseEngine:
    def __init__(self, predictor: Predictor | None = None, labels: list[str] | None = None,
                 conf_threshold: float = 0.5):
        self.predictor = predictor
        self.labels = [parse_label(x) for x in (labels or [])]
        self.conf_threshold = conf_threshold

    @classmethod
    def from_dir(cls, model_dir: Path, conf_threshold: float = 0.5) -> "DiseaseEngine":
        model_path, labels_path = Path(model_dir) / "disease_model.pt", Path(model_dir) / "labels.json"
        if not (model_path.exists() and labels_path.exists()):
            return cls(conf_threshold=conf_threshold)
        try:
            labels = json.loads(labels_path.read_text())
            return cls(TorchPredictor(model_path), labels, conf_threshold)
        except Exception as exc:  # torch missing, corrupt file, ...
            print(f"[disease] model not loaded: {exc}")
            return cls(conf_threshold=conf_threshold)

    @property
    def ready(self) -> bool:
        return self.predictor is not None and bool(self.labels)

    @property
    def crops(self) -> list[str]:
        return sorted({l.crop for l in self.labels})

    def analyze(self, image: Image.Image, crop: str) -> DiseaseResult:
        if not self.ready:
            raise RuntimeError("Disease model is not loaded")
        idx = [i for i, l in enumerate(self.labels) if l.crop.lower() == crop.lower()]
        if not idx:
            raise ValueError(f"No trained classes for crop '{crop}'")
        logits = np.asarray(self.predictor.predict(image), dtype=np.float64)
        probs = _softmax(logits[idx])                        # only the selected crop's classes
        order = np.argsort(-probs)
        best = self.labels[idx[order[0]]]
        conf = float(probs[order[0]])
        crop_name = best.crop

        if best.healthy:
            sev, pct, actions = "None", 0.0, list(knowledge.HEALTHY_ACTIONS)
        else:
            pct = lesion_percent(image)
            sev = severity_label(pct)
            actions = knowledge.disease_actions(best.disease, crop_name)
        alts = [{"disease": self.labels[idx[j]].disease, "probability": round(float(probs[j]), 4)}
                for j in order[:3]]
        return DiseaseResult(
            crop=crop_name, healthy=best.healthy, disease=best.disease, confidence=round(conf, 4),
            severity=sev, severity_pct=round(pct, 1), actions=actions,
            uncertain=conf < self.conf_threshold, alternatives=alts,
        )
