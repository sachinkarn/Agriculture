"""API tests. Needs the web dependencies:  pip install -r ../requirements.txt httpx
Run:  python -m unittest tests.test_api -v      (skipped automatically if FastAPI is not installed)
"""
import importlib.util
import io
import os
import tempfile
import unittest

HAVE_WEB = all(importlib.util.find_spec(m) for m in ("fastapi", "sqlalchemy", "httpx", "multipart"))

if HAVE_WEB:
    os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.gettempdir()}/kisanmitra_test.db"
    os.environ["MODEL_DIR"] = tempfile.mkdtemp()            # empty folder -> no disease model
    from fastapi.testclient import TestClient
    from PIL import Image

    from app.main import app
    from tests.test_services import LABELS, StubPredictor, leaf
    from app.services.disease import DiseaseEngine


def png(img) -> bytes:
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


@unittest.skipUnless(HAVE_WEB, "FastAPI stack not installed")
class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client_cm = TestClient(app)
        cls.client = cls.client_cm.__enter__()          # runs startup (creates tables)

    @classmethod
    def tearDownClass(cls):
        cls.client_cm.__exit__(None, None, None)

    def test_health_without_model(self):
        app.state.disease = DiseaseEngine()
        j = self.client.get("/api/health").json()
        self.assertEqual(j["status"], "ok")
        self.assertFalse(j["disease_model_ready"])

    def test_crop_analyze_503_without_model(self):
        app.state.disease = DiseaseEngine()
        r = self.client.post("/api/crop/analyze", data={"crop": "Apple"},
                             files={"file": ("a.png", png(leaf(0.1)), "image/png")})
        self.assertEqual(r.status_code, 503)

    def test_crop_analyze_with_stub_model(self):
        app.state.disease = DiseaseEngine(StubPredictor("Apple___Apple_scab"), LABELS)
        r = self.client.post("/api/crop/analyze", data={"crop": "apple"},
                             files={"file": ("a.png", png(leaf(0.12)), "image/png")})
        self.assertEqual(r.status_code, 200, r.text)
        j = r.json()
        self.assertEqual((j["disease"], j["healthy"], j["severity"]), ("Apple scab", False, "Medium"))
        self.assertIn("id", j)

    def test_bad_inputs(self):
        app.state.disease = DiseaseEngine(StubPredictor("Apple___Apple_scab"), LABELS)
        r = self.client.post("/api/crop/analyze", data={"crop": "Banana"},
                             files={"file": ("a.png", png(leaf(0.1)), "image/png")})
        self.assertEqual(r.status_code, 422)
        r = self.client.post("/api/crop/analyze", data={"crop": "Apple"},
                             files={"file": ("a.txt", b"not an image", "text/plain")})
        self.assertEqual(r.status_code, 400)

    def test_irrigation_soil_recommend(self):
        j = self.client.post("/api/irrigation/advise", json={"crop": "Rice", "soil_moisture": 20,
                             "temperature": 36, "humidity": 60, "rain_probability": 10}).json()
        self.assertEqual((j["title"], j["mm"]), ("Irrigate now", 25))
        self.assertEqual(self.client.post("/api/soil/analyze", json={}).json()["score"], 85)
        top = self.client.post("/api/crops/recommend", json={"water": "M"}).json()["crops"]
        self.assertEqual(top[0]["crop"], "Apple")
        self.assertEqual(self.client.post("/api/irrigation/advise", json={"soil_moisture": 150}).status_code, 422)

    def test_plan_and_history(self):
        self.client.delete("/api/history")
        p = self.client.post("/api/plan", json={"crop": "Apple", "disease": "Apple scab", "severity": "Medium",
                             "confidence": 0.91, "temperature": 31, "humidity": 78, "rain_probability": 20}).json()
        self.assertEqual(p["farm_health"], 74)
        h = self.client.get("/api/history").json()
        self.assertEqual(len(h), 1)
        self.assertEqual(h[0]["type"], "plan")
        self.assertEqual(self.client.delete("/api/history").json()["deleted"], 1)


if __name__ == "__main__":
    unittest.main()
