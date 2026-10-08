"""Soil scoring and fertilizer advice (same rules as the prototype's Soil analysis page)."""


def analyze_soil(n: float, p: float, k: float, ph: float, m: float) -> dict:
    score = 100
    advice: list[str] = []
    problems: list[str] = []
    fert: list[str] = []

    levels = {
        "n": "Low" if n < 280 else "High" if n > 450 else "Good",
        "p": "Low" if p < 11 else "Good",
        "k": "Low" if k < 110 else "Good",
        "ph": "Acidic" if ph < 5.8 else "Alkaline" if ph > 7.8 else "Optimal",
    }

    if n < 280:
        score -= 15
        problems.append("Nitrogen is low")
        fert.append("Apply urea in two small splits")
        advice.append("Nitrogen is low: apply urea in two small splits instead of one heavy dose.")
    elif n > 450:
        score -= 8
        problems.append("Nitrogen is high")
        fert.append("Skip nitrogen top-dressing")
        advice.append("Nitrogen is high: skip nitrogen top-dressing this round.")
    if p < 11:
        score -= 15
        problems.append("Phosphorus is low")
        fert.append("Add DAP or SSP at sowing")
        advice.append("Phosphorus is low: add DAP or SSP at sowing.")
    if k < 110:
        score -= 12
        problems.append("Potassium is low")
        fert.append("Add muriate of potash")
        advice.append("Potassium is low: add muriate of potash.")
    if ph < 5.8:
        score -= 14
        problems.append("Soil is acidic")
        fert.append("Add agricultural lime")
        advice.append("Soil is acidic: add agricultural lime before sowing.")
    elif ph > 7.8:
        score -= 14
        problems.append("Soil is alkaline")
        fert.append("Add gypsum or organic matter")
        advice.append("Soil is alkaline: add gypsum or organic matter.")
    if not advice:
        advice.append("Nutrients look balanced. Skip extra fertilizer and re-test next season.")

    return {
        "score": max(35, score),
        "levels": levels,
        "moisture": m,
        "problems": problems,
        "main_concern": problems[0] if problems else "None. Nutrients look balanced",
        "fertilizer": fert[0] if fert else "No extra fertilizer needed",
        "advice": advice,
    }
