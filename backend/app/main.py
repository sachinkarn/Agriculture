"""KisanMitra AI backend.

Run from the `backend` folder:   uvicorn app.main:app --reload
Open:                            http://localhost:8000        (the web app)
                                 http://localhost:8000/docs   (interactive API docs)
"""
import io
import json
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from .config import settings
from .database import Base, engine, get_db
from .models import Analysis
from .schemas import IrrigationIn, PlanIn, RecommendIn, SoilIn
from .services import knowledge
from .services.disease import DiseaseEngine
from .services.irrigation import advise_irrigation
from .services.plan import build_plan
from .services.recommend import recommend_crops
from .services.soil import analyze_soil
from .services.weather import fetch_weather

Image.MAX_IMAGE_PIXELS = 50_000_000   # refuse decompression bombs


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    app.state.disease = DiseaseEngine.from_dir(settings.model_dir, settings.conf_threshold)
    print(f"[startup] disease model ready: {app.state.disease.ready}")
    yield


app = FastAPI(title="KisanMitra AI", version="1.0.0", lifespan=lifespan,
              description="Turns crop photos, soil values and weather into a simple farm plan.")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins,
                   allow_methods=["*"], allow_headers=["*"])


def _log(db: Session, kind: str, crop: str | None, summary: str, payload: dict) -> int:
    row = Analysis(kind=kind, crop=crop, summary=summary[:255], payload=json.dumps(payload))
    db.add(row)
    db.commit()
    return row.id


# --------------------------------------------------------------------------- health
@app.get("/api/health")
def health():
    d: DiseaseEngine = app.state.disease
    return {"status": "ok", "disease_model_ready": d.ready, "disease_crops": d.crops,
            "supported_crops": knowledge.SUPPORTED_CROPS}


# --------------------------------------------------------------------------- crop photo
@app.post("/api/crop/analyze")
async def crop_analyze(file: UploadFile = File(...), crop: str = Form("Apple"),
                       db: Session = Depends(get_db)):
    disease: DiseaseEngine = app.state.disease
    if not disease.ready:
        raise HTTPException(503, "Disease model not found. Train it with ml/train_disease.py "
                                 "and place disease_model.pt + labels.json in backend/models/.")
    crop = crop.strip().title()
    if crop not in disease.crops:
        raise HTTPException(422, f"Unsupported crop '{crop}'. Supported: {', '.join(disease.crops)}")

    data = await file.read()
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"Photo is larger than {settings.max_upload_mb} MB")
    try:
        image = Image.open(io.BytesIO(data))
        image.load()
        image = ImageOps.exif_transpose(image).convert("RGB")
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise HTTPException(400, "That file is not a readable image")
    image.thumbnail((1024, 1024))

    result = await run_in_threadpool(disease.analyze, image, crop)
    out = result.to_dict()
    label = "Healthy" if result.healthy else f"{result.disease} ({result.severity})"
    out["id"] = _log(db, "crop", result.crop, f"{result.crop}: {label}", out)
    return out


# --------------------------------------------------------------------------- irrigation
@app.post("/api/irrigation/advise")
def irrigation(body: IrrigationIn, db: Session = Depends(get_db)):
    out = advise_irrigation(body.crop, body.soil_moisture, body.temperature, body.humidity,
                            body.rain_probability, body.diseased)
    out["id"] = _log(db, "irrigation", body.crop, f"{body.crop}: {out['title']}", out)
    return out


# --------------------------------------------------------------------------- soil
@app.post("/api/soil/analyze")
def soil(body: SoilIn, db: Session = Depends(get_db)):
    out = analyze_soil(body.n, body.p, body.k, body.ph, body.m)
    out["id"] = _log(db, "soil", None, f"Soil score {out['score']}: {out['main_concern']}", out)
    return out


# --------------------------------------------------------------------------- recommendations
@app.post("/api/crops/recommend")
def recommend(body: RecommendIn):
    return {"crops": recommend_crops(body.soil.n, body.soil.ph, body.water),
            "fertilizer_plan": analyze_soil(**body.soil.model_dump())["advice"]}


# --------------------------------------------------------------------------- weather
@app.get("/api/weather")
def weather(lat: float | None = None, lon: float | None = None, fresh: bool = False):
    w = fetch_weather(lat, lon, fresh=fresh)
    if not w:
        raise HTTPException(503, "Weather service not reachable")
    return JSONResponse(w, headers={"Cache-Control": "no-store"})


# --------------------------------------------------------------------------- today's plan
@app.post("/api/plan")
def plan(body: PlanIn, db: Session = Depends(get_db)):
    given = (body.temperature, body.humidity, body.rain_probability)
    if all(v is not None for v in given):
        wx = {"temperature": body.temperature, "humidity": body.humidity,
              "rain_probability": body.rain_probability, "source": "request"}
    elif body.latitude is not None and body.longitude is not None:
        wx = fetch_weather(body.latitude, body.longitude)       # None -> defaults inside build_plan
    else:
        wx = None
    out = build_plan(body.crop, body.disease, body.confidence, body.severity,
                     body.soil.model_dump(), wx)
    out["id"] = _log(db, "plan", body.crop, f"Plan for {body.crop}: {out['rows'][2]['value']}", out)
    return out


# --------------------------------------------------------------------------- history
@app.get("/api/history")
def history(limit: int = 50, db: Session = Depends(get_db)):
    rows = db.scalars(select(Analysis).order_by(Analysis.id.desc()).limit(min(limit, 200))).all()
    return [{"id": r.id, "when": r.created_at.isoformat(), "type": r.kind,
             "crop": r.crop, "result": r.summary} for r in rows]


@app.delete("/api/history")
def clear_history(db: Session = Depends(get_db)):
    deleted = db.query(Analysis).delete()
    db.commit()
    return {"deleted": deleted}


# --------------------------------------------------------------------------- web app (keep last)
if settings.frontend_dir.exists():
    app.mount("/", StaticFiles(directory=settings.frontend_dir, html=True), name="frontend")
