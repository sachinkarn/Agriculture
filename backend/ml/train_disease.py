"""Train the crop disease classifier and export it for the API.

Usage (from the `backend` folder):
    pip install -r ../requirements-ml.txt
    python -m ml.train_disease --data /path/to/PlantVillage --epochs 5

`--data` must contain one sub-folder per class, named like the public PlantVillage dataset, e.g.
    Apple___Apple_scab/  Apple___healthy/  Corn_(maize)___Northern_Leaf_Blight/
    Orange___Haunglongbing_(Citrus_greening)/  Potato___Late_blight/  ...
Only the four crops the prototype supports (Apple, Corn, Orange, Potato) are used.

Output (in --out, default backend/models):
    disease_model.pt   TorchScript model, input 1x3x224x224, output = class logits
    labels.json        class names in output order
    metrics.json       validation accuracy (overall and per class)

Model: MobileNetV2 pretrained on ImageNet. The backbone is frozen and only the final layer is
trained, which is fast on a laptop CPU/GPU. Needs internet once to download the ImageNet weights.
"""
import argparse
import json
import random
from pathlib import Path

import torch
import torch.nn as nn
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from torchvision import datasets, models, transforms

CROP_PREFIXES = ("Apple___", "Corn_(maize)___", "Orange___", "Potato___")
MEAN, STD = [0.485, 0.456, 0.406], [0.229, 0.224, 0.225]


class Photos(Dataset):
    def __init__(self, samples, tf):
        self.samples, self.tf = samples, tf

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, i):
        path, label = self.samples[i]
        return self.tf(Image.open(path).convert("RGB")), label


def evaluate(model, loader, device, n_classes):
    model.eval()
    correct = torch.zeros(n_classes)
    total = torch.zeros(n_classes)
    with torch.no_grad():
        for x, y in loader:
            pred = model(x.to(device)).argmax(1).cpu()
            for t, p in zip(y, pred):
                total[t] += 1
                correct[t] += int(t == p)
    return correct.sum().item() / max(total.sum().item(), 1), (correct / total.clamp(min=1)).tolist()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="folder with one sub-folder per class")
    ap.add_argument("--out", default=str(Path(__file__).resolve().parents[1] / "models"))
    ap.add_argument("--epochs", type=int, default=5)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--val-split", type=float, default=0.2)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    random.seed(args.seed)
    torch.manual_seed(args.seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"

    base = datasets.ImageFolder(args.data)
    classes = [c for c in base.classes if c.startswith(CROP_PREFIXES)]
    if not classes:
        raise SystemExit("No Apple/Corn/Orange/Potato class folders found in --data")
    remap = {base.class_to_idx[c]: i for i, c in enumerate(classes)}
    samples = [(p, remap[y]) for p, y in base.samples if y in remap]
    random.shuffle(samples)
    n_val = int(len(samples) * args.val_split)
    val_s, train_s = samples[:n_val], samples[n_val:]
    print(f"{len(classes)} classes, {len(train_s)} train / {len(val_s)} validation photos, device={device}")

    tf_train = transforms.Compose([
        transforms.RandomResizedCrop(224, scale=(0.7, 1.0)), transforms.RandomHorizontalFlip(),
        transforms.ColorJitter(0.2, 0.2, 0.2), transforms.ToTensor(), transforms.Normalize(MEAN, STD)])
    tf_eval = transforms.Compose([
        transforms.Resize(256), transforms.CenterCrop(224), transforms.ToTensor(), transforms.Normalize(MEAN, STD)])
    train_dl = DataLoader(Photos(train_s, tf_train), batch_size=args.batch, shuffle=True, num_workers=args.workers)
    val_dl = DataLoader(Photos(val_s, tf_eval), batch_size=args.batch, num_workers=args.workers)

    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)
    for p in model.features.parameters():
        p.requires_grad = False
    model.classifier[1] = nn.Linear(model.last_channel, len(classes))
    model.to(device)
    opt = torch.optim.Adam(model.classifier.parameters(), lr=args.lr)
    loss_fn = nn.CrossEntropyLoss()

    best_acc, best_state, best_per_class = 0.0, None, []
    for epoch in range(1, args.epochs + 1):
        model.train()
        running = 0.0
        for x, y in train_dl:
            x, y = x.to(device), y.to(device)
            opt.zero_grad()
            loss = loss_fn(model(x), y)
            loss.backward()
            opt.step()
            running += loss.item() * len(y)
        acc, per_class = evaluate(model, val_dl, device, len(classes))
        print(f"epoch {epoch}/{args.epochs}  train loss {running / max(len(train_s), 1):.4f}  val accuracy {acc:.4f}")
        if acc >= best_acc:
            best_acc, best_per_class = acc, per_class
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}

    model.load_state_dict(best_state)
    model.to("cpu").eval()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    torch.jit.script(model).save(str(out / "disease_model.pt"))
    (out / "labels.json").write_text(json.dumps(classes, indent=2))
    (out / "metrics.json").write_text(json.dumps({
        "val_accuracy": round(best_acc, 4),
        "per_class_accuracy": {c: round(a, 4) for c, a in zip(classes, best_per_class)},
        "train_photos": len(train_s), "val_photos": len(val_s), "epochs": args.epochs,
        "note": "Validation split comes from the same dataset, so field accuracy will be lower.",
    }, indent=2))
    print(f"saved model to {out}  (best val accuracy {best_acc:.4f})")


if __name__ == "__main__":
    main()
