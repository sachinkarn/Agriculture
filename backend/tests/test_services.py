"""Unit tests for the decision logic. No web framework needed:  python -m unittest discover -s tests -v"""
import unittest

import numpy as np
from PIL import Image, ImageDraw

from app.services import knowledge
from app.services.disease import DiseaseEngine, parse_label, preprocess
from app.services.irrigation import advise_irrigation
from app.services.plan import build_plan, crop_score
from app.services.recommend import recommend_crops
from app.services.severity import lesion_percent, severity_label
from app.services.soil import analyze_soil

LABELS = [
    "Apple___Apple_scab", "Apple___Black_rot", "Apple___Cedar_apple_rust", "Apple___healthy",
    "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot", "Corn_(maize)___Common_rust_",
    "Corn_(maize)___Northern_Leaf_Blight", "Corn_(maize)___healthy",
    "Orange___Haunglongbing_(Citrus_greening)",
    "Potato___Early_blight", "Potato___Late_blight", "Potato___healthy",
]


def leaf(spot_fraction: float) -> Image.Image:
    """Green leaf-coloured image with a brown block covering `spot_fraction` of the area."""
    img = Image.new("RGB", (200, 200), (60, 150, 70))
    side = int(200 * spot_fraction ** 0.5)
    x0 = (200 - side) // 2
    ImageDraw.Draw(img).rectangle([x0, x0, x0 + side, x0 + side], fill=(140, 90, 40))
    return img


class StubPredictor:
    def __init__(self, favourite: str, strength: float = 6.0):
        self.fav, self.strength = favourite, strength

    def predict(self, image):
        logits = np.zeros(len(LABELS))
        logits[LABELS.index(self.fav)] = self.strength
        return logits


class SoilTests(unittest.TestCase):
    def test_default_soil(self):
        r = analyze_soil(240, 14, 130, 6.4, 45)
        self.assertEqual(r["score"], 85)                      # only nitrogen is low: 100 - 15
        self.assertEqual(r["main_concern"], "Nitrogen is low")
        self.assertEqual(r["fertilizer"], "Apply urea in two small splits")

    def test_balanced_and_floor(self):
        self.assertEqual(analyze_soil(300, 20, 150, 6.5, 40)["fertilizer"], "No extra fertilizer needed")
        worst = analyze_soil(100, 2, 40, 4.0, 10)             # 100-15-15-12-14 = 44
        self.assertEqual(worst["score"], 44)
        self.assertEqual(len(worst["problems"]), 4)

    def test_ph_levels(self):
        self.assertEqual(analyze_soil(300, 20, 150, 5.0, 40)["levels"]["ph"], "Acidic")
        self.assertEqual(analyze_soil(300, 20, 150, 8.2, 40)["levels"]["ph"], "Alkaline")


class RecommendTests(unittest.TestCase):
    def test_ranking_matches_prototype(self):
        # Worked out by hand from the prototype's scoring rule (N=240, pH 6.4, medium water).
        top = recommend_crops(240, 6.4, "M")
        self.assertEqual([(c["crop"], c["match"]) for c in top],
                         [("Apple", 92), ("Orange", 92), ("Corn", 84), ("Potato", 84)])

    def test_scores_are_bounded(self):
        for c in recommend_crops(900, 3.0, "L", top=7):
            self.assertTrue(30 <= c["match"] <= 98)


class IrrigationTests(unittest.TestCase):
    def test_rain_beats_everything(self):
        r = advise_irrigation("Rice", 10, 40, 50, 70)
        self.assertEqual((r["title"], r["mm"], r["save"]), ("Do not irrigate today", 0, 25))

    def test_wet_soil(self):
        r = advise_irrigation("Rice", 60, 31, 78, 20)
        self.assertEqual((r["title"], r["save"], r["time"]), ("Do not irrigate today", 18, "Recheck tomorrow morning"))

    def test_dry_soil_and_heat(self):
        r = advise_irrigation("Rice", 20, 36, 60, 10)
        self.assertEqual((r["title"], r["mm"], r["go"]), ("Irrigate now", 25, True))
        self.assertEqual(advise_irrigation("Rice", 20, 30, 60, 10)["mm"], 20)

    def test_moderate_and_disease_note(self):
        r = advise_irrigation("Apple", 45, 31, 78, 20, diseased=True)
        self.assertEqual((r["title"], r["mm"]), ("Light irrigation this evening", 10))
        self.assertIn("Water at the base", r["why"])
        self.assertNotIn("Water at the base", advise_irrigation("Apple", 45, 31, 50, 20, diseased=True)["why"])


class SeverityTests(unittest.TestCase):
    def test_healthy_leaf_has_no_lesion(self):
        self.assertLess(lesion_percent(leaf(0.0)), 1)

    def test_big_lesion_is_high(self):
        pct = lesion_percent(leaf(0.30))
        self.assertGreater(pct, 20)
        self.assertEqual(severity_label(pct), "High")

    def test_labels(self):
        self.assertEqual([severity_label(x) for x in (0, 7.9, 8, 19.9, 20)],
                         ["Low", "Low", "Medium", "Medium", "High"])

    def test_blank_image(self):
        self.assertEqual(lesion_percent(Image.new("RGB", (100, 100), (255, 255, 255))), 0.0)


class DiseaseTests(unittest.TestCase):
    def engine(self, fav, strength=6.0, threshold=0.5):
        return DiseaseEngine(StubPredictor(fav, strength), LABELS, threshold)

    def test_parse_label(self):
        self.assertEqual(parse_label("Apple___Apple_scab").disease, "Apple scab")
        self.assertEqual(parse_label("Corn_(maize)___Northern_Leaf_Blight").crop, "Corn")
        self.assertEqual(parse_label("Corn_(maize)___Northern_Leaf_Blight").disease, "Northern leaf blight")
        self.assertEqual(parse_label("Orange___Haunglongbing_(Citrus_greening)").disease, "Citrus greening")
        self.assertEqual(parse_label("Corn_(maize)___Common_rust_").disease, "Common rust")
        self.assertEqual(parse_label("Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot").disease, "Gray leaf spot")
        h = parse_label("Potato___healthy")
        self.assertTrue(h.healthy)
        self.assertEqual(h.disease, "Healthy")

    def test_diseased_apple(self):
        r = self.engine("Apple___Apple_scab").analyze(leaf(0.12), "Apple")
        self.assertEqual((r.crop, r.disease, r.healthy), ("Apple", "Apple scab", False))
        self.assertGreater(r.confidence, 0.9)
        self.assertEqual(r.severity, "Medium")
        self.assertEqual(r.actions, knowledge.DISEASE_INFO["Apple scab"][1])
        self.assertFalse(r.uncertain)
        self.assertEqual(r.alternatives[0]["disease"], "Apple scab")

    def test_healthy_leaf(self):
        r = self.engine("Potato___healthy").analyze(leaf(0.0), "potato")
        self.assertTrue(r.healthy)
        self.assertEqual((r.severity, r.severity_pct), ("None", 0.0))
        self.assertEqual(r.actions, knowledge.HEALTHY_ACTIONS)

    def test_only_selected_crop_is_considered(self):
        # Model "thinks" Apple scab, but the farmer said Potato: answer must be a potato class.
        r = self.engine("Apple___Apple_scab").analyze(leaf(0.1), "Potato")
        self.assertEqual(r.crop, "Potato")
        self.assertIn(r.disease, {"Early blight", "Late blight", "Healthy"})

    def test_low_confidence_is_flagged(self):
        r = self.engine("Apple___Apple_scab", strength=0.0).analyze(leaf(0.1), "Apple")   # all classes equal
        self.assertTrue(r.uncertain)
        self.assertAlmostEqual(r.confidence, 0.25, places=2)                              # 4 apple classes

    def test_unknown_crop_and_no_model(self):
        with self.assertRaises(ValueError):
            self.engine("Apple___Apple_scab").analyze(leaf(0.1), "Banana")
        empty = DiseaseEngine()
        self.assertFalse(empty.ready)
        with self.assertRaises(RuntimeError):
            empty.analyze(leaf(0.1), "Apple")

    def test_preprocess_shape(self):
        a = preprocess(leaf(0.1))
        self.assertEqual(a.shape, (1, 3, 224, 224))
        self.assertEqual(a.dtype, np.float32)

    def test_result_is_json_ready(self):
        import json
        json.dumps(self.engine("Corn_(maize)___Common_rust_").analyze(leaf(0.05), "Corn").to_dict())


class PlanTests(unittest.TestCase):
    SOIL = dict(n=240, p=14, k=130, ph=6.4, m=45)

    def test_crop_score(self):
        self.assertEqual(crop_score(True, 96, "None"), 94)
        self.assertEqual(crop_score(False, 91, "Medium"), 69)       # 100 - 22 - 9
        self.assertEqual(crop_score(False, 40, "High"), 40)         # floored at 40

    def test_diseased_fungal_plan(self):
        p = build_plan("Apple", "Apple scab", 0.91, "Medium", self.SOIL, None)
        rows = {r["label"]: r["value"] for r in p["rows"]}
        self.assertEqual(rows["Risk"], "Apple scab, Medium severity")
        self.assertEqual(rows["Fertilizer"], "Avoid additional nitrogen")        # fungal -> no extra nitrogen
        self.assertEqual(rows["Next check"], "In 48 hours")
        self.assertEqual(rows["Check"], "Remove and destroy fallen infected leaves")
        self.assertEqual(p["farm_health"], 74)                                   # 69*0.7 + 85*0.3 = 73.8

    def test_healthy_plan(self):
        p = build_plan("Potato", None, 0.96, None, self.SOIL, None)
        rows = {r["label"]: r["value"] for r in p["rows"]}
        self.assertEqual(rows["Risk"], "No disease signs found")
        self.assertEqual(rows["Fertilizer"], "Apply urea in two small splits")   # from soil, not disease
        self.assertEqual(rows["Next check"], "In 7 days")

    def test_rain_changes_water_row(self):
        wx = {"temperature": 30, "humidity": 85, "rain_probability": 80, "source": "test"}
        p = build_plan("Apple", "Apple scab", 0.9, "Low", self.SOIL, wx)
        self.assertEqual(p["rows"][2]["value"], "Do not irrigate today")
        self.assertEqual(p["estimated_water_saving_pct"], 25)


class WeatherCacheTests(unittest.TestCase):
    def test_fresh_bypasses_cache(self):
        import io, json
        from unittest import mock
        from app.services import weather as wx
        payload = {"current": {"temperature_2m": 30.0, "relative_humidity_2m": 70.0},
                   "daily": {"precipitation_probability_max": [20]}}
        calls = []

        def fake_open(url, timeout=None):
            calls.append(url)
            return io.StringIO(json.dumps(payload))

        wx._CACHE.clear()
        with mock.patch.object(wx.urllib.request, "urlopen", fake_open):
            wx.fetch_weather(10.9, 79.8)
            wx.fetch_weather(10.9, 79.8)                 # served from cache
            self.assertEqual(len(calls), 1)
            wx.fetch_weather(10.9, 79.8, fresh=True)     # always hits the network
            self.assertEqual(len(calls), 2)
        wx._CACHE.clear()


if __name__ == "__main__":
    unittest.main()
