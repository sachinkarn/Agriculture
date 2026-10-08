"""The decision engine: combine crop health, soil and weather into one plain-language plan.

Same output as the prototype's "Today's farm plan" card.
"""
from . import knowledge
from .irrigation import advise_irrigation
from .soil import analyze_soil

DEFAULT_WEATHER = {"temperature": 31.0, "humidity": 78.0, "rain_probability": 20.0, "source": "default"}


def crop_score(healthy: bool, confidence_pct: float, severity: str | None) -> int:
    if healthy:
        return 94
    penalty = {"Low": 12, "Medium": 22, "High": 38}.get(severity or "", 0)
    return int(max(40, 100 - penalty - (100 - confidence_pct)))


def build_plan(crop: str, disease: str | None, confidence: float, severity: str | None,
               soil: dict, weather: dict | None) -> dict:
    weather = weather or DEFAULT_WEATHER
    healthy = disease is None or disease.lower() == "healthy"
    soil_res = analyze_soil(**soil)
    sev = "None" if healthy else (severity or "Medium")
    conf_pct = round(confidence * 100)

    irr = advise_irrigation(crop, soil["m"], weather["temperature"], weather["humidity"],
                            weather["rain_probability"], diseased=not healthy)
    actions = knowledge.HEALTHY_ACTIONS if healthy else knowledge.disease_actions(disease, crop)
    fungal = (not healthy) and knowledge.disease_type(disease, crop) == "fungal"

    health = round(crop_score(healthy, conf_pct, sev) * 0.7 + soil_res["score"] * 0.3)
    rows = [
        {"icon": "🌱", "label": "Crop", "value": crop},
        {"icon": "⚠️", "label": "Risk",
         "value": "No disease signs found" if healthy else f"{disease}, {sev} severity"},
        {"icon": "💧", "label": "Water", "value": irr["title"]},
        {"icon": "🧪", "label": "Fertilizer",
         "value": "Avoid additional nitrogen" if fungal else soil_res["fertilizer"]},
        {"icon": "👀", "label": "Check", "value": actions[0]},
        {"icon": "📅", "label": "Next check", "value": "In 7 days" if healthy else "In 48 hours"},
    ]
    return {
        "farm_health": health,
        "soil_score": soil_res["score"],
        "rows": rows,
        "irrigation": irr,
        "soil": soil_res,
        "actions": actions,
        "weather": weather,
        "estimated_water_saving_pct": irr["save"],
        "note": "Scores and savings are model estimates, not guarantees.",
    }
