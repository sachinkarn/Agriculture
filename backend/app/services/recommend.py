"""Crop suitability ranking (same scoring as the prototype's Recommendations page)."""

# name, (pH low, pH high), nitrogen need, water need   (L / M / H)
CROPS = [
    ("Apple", (5.5, 6.5), "M", "M"),
    ("Corn", (5.8, 7.0), "H", "M"),
    ("Orange", (6.0, 7.5), "M", "M"),
    ("Potato", (5.0, 6.5), "H", "M"),
    ("Sugarcane", (6.0, 7.5), "H", "H"),
]
LEVEL = {"L": 1, "M": 2, "H": 3}


def _round(x: float) -> int:
    return int(x + 0.5)          # round half up, like JavaScript's Math.round for positives


def recommend_crops(n: float, ph: float, water: str, top: int = 4) -> list[dict]:
    n_level = 1 if n < 280 else 2 if n < 450 else 3
    ranked = []
    for name, (lo, hi), n_need, w_need in CROPS:
        score = 40.0
        if lo <= ph <= hi:
            score += 30
        else:
            score += max(0.0, 30 - min(abs(ph - lo), abs(ph - hi)) * 15)
        score += 20 - abs(n_level - LEVEL[n_need]) * 8
        score += 10 - abs(LEVEL[water] - LEVEL[w_need]) * 5
        ranked.append({"crop": name, "match": _round(max(30, min(98, score)))})
    ranked.sort(key=lambda r: -r["match"])
    return ranked[:top]
