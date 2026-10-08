# KisanMitra AI

A practical AI companion for smarter, more sustainable farming. It turns a leaf photo, soil
values and weather into one plain-language plan: **what to do, what to avoid, what to monitor.**

```
kisanmitra-ai/
├── frontend/                  the web app (plain HTML/CSS/JS, no build step)
│   ├── index.html             page shell + script load order
│   ├── css/styles.css
│   └── js/
│       ├── core/              config, state, utils, router
│       ├── data/              nav pages, diseases, crops, sample weather
│       ├── services/          soil scoring, weather loading
│       ├── components/        reusable HTML helpers (ring, list, soil card, decision)
│       ├── pages/             one file per page (view + handlers)
│       └── main.js            startup
├── backend/
│   ├── app/
│   │   ├── main.py            FastAPI routes
│   │   ├── services/          decision logic: disease, severity, irrigation, soil, recommend, plan, weather
│   │   ├── models.py          database table (analyses)
│   │   └── database.py        SQLite by default, PostgreSQL via DATABASE_URL
│   ├── ml/train_disease.py    trains the disease model (PyTorch, MobileNetV2)
│   ├── models/                put disease_model.pt + labels.json here
│   └── tests/                 unit + API tests
├── requirements*.txt, Dockerfile, docker-compose.yml, .env.example
```

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd backend
uvicorn app.main:app --reload
```

Open **http://localhost:8000** for the app and **http://localhost:8000/docs** for the API docs.

Without a trained disease model everything works except real photo analysis: the web app
falls back to its labelled **Demo prediction** (with a red banner saying why), and `POST /api/crop/analyze` returns `503`.
When the app is served by the backend, the dashboard and irrigation sliders use live weather from `/api/weather`
(Open-Meteo, set `DEFAULT_LAT` / `DEFAULT_LON` for your village), irrigation advice goes through `/api/irrigation/advise`,
and results below `CONF_THRESHOLD` are shown with a "Low confidence" warning.
Nothing is ever shown as a "model prediction" unless a real model produced it.

## Train the disease model (the AI part)

1. Download the public **PlantVillage** dataset (e.g. from Kaggle). Class folders must be named like
   `Apple___Apple_scab`, `Corn_(maize)___Northern_Leaf_Blight`, `Potato___Late_blight`, `Orange___Haunglongbing_(Citrus_greening)` ...
2. Install PyTorch (CPU build is fine): `pip install -r requirements-ml.txt`
3. From `backend/`:
   ```bash
   python -m ml.train_disease --data /path/to/PlantVillage --epochs 5
   ```
4. This writes `disease_model.pt`, `labels.json` and `metrics.json` into `backend/models/`.
   Restart the server. `GET /api/health` should now show `"disease_model_ready": true`.

Supported crops: Apple, Corn, Orange, Potato (the four with classes in PlantVillage that the web app offers).
Read `metrics.json` before quoting any accuracy. PlantVillage photos are taken on plain backgrounds, so
accuracy on real field photos will be lower than the validation number.

## API

| Method | Path | What it does |
|---|---|---|
| GET | `/api/health` | status, whether the disease model is loaded |
| POST | `/api/crop/analyze` | multipart: `file` (leaf photo), `crop` → disease, confidence, severity, actions |
| POST | `/api/irrigation/advise` | crop, soil moisture, temperature, humidity, rain % → water or not, how much, when |
| POST | `/api/soil/analyze` | N, P, K, pH, moisture → soil score, fertilizer advice |
| POST | `/api/crops/recommend` | soil + water level → best-matching crops |
| POST | `/api/plan` | combines crop result + soil + weather into "Today's farm plan" |
| GET | `/api/weather?lat=&lon=&fresh=` | current weather from Open-Meteo (needs internet); cached 10 min unless `fresh=1`; the dashboard always sends `fresh=1` |
| GET / DELETE | `/api/history` | past analyses stored in the database |

## How each module works (be honest about this in Q&A)

| Module | Method |
|---|---|
| Disease detection | **Trained model** (MobileNetV2 transfer learning), probabilities restricted to the selected crop. Flags `uncertain` below `CONF_THRESHOLD` (default 50%). |
| Severity | **Image processing**, not a model: share of non-green pixels inside the leaf area. Fooled by brown soil or hands in the frame. |
| Irrigation | **Transparent rules** (rain chance, soil moisture, heat, humidity). Same rules as the web app. |
| Soil / fertilizer | **Threshold rules** on N, P, K and pH. |
| Crop recommendation | **Scoring rule** on pH, nitrogen and water. |

Rules were kept on purpose where no training data exists: they are explainable and can be swapped for
a trained model later without changing the API (each lives in its own file under `app/services/`).
Water-saving figures and the farm-health score are **estimates, not measured results**.

## Tests

```bash
cd backend
python -m unittest discover -s tests -v       # logic tests, no web framework needed
pip install httpx && python -m unittest tests.test_api -v   # API tests
```

## PostgreSQL / Docker

```bash
docker compose up --build        # app + PostgreSQL on http://localhost:8000
```
Or set `DATABASE_URL=postgresql://user:pass@host:5432/db` and `pip install -r requirements-postgres.txt`.

## Limits and next steps

- Advice is general guidance for a prototype. It does not recommend chemicals or doses; farmers should
  confirm with a local agriculture officer.
- No user accounts or farm profiles yet (the history table is shared). Add auth before real deployment.
- Roadmap from the deck: regional-language UI, voice assistant, IoT soil sensors, satellite signals.
