"""Current weather from Open-Meteo (free, no API key). Falls back to sample weather when offline."""
import json
import time
import urllib.parse
import urllib.request

from ..config import settings

_CACHE: dict[tuple[float, float], tuple[float, dict]] = {}
_TTL_S = 600

_SAMPLES = [
    {"temperature": 33.0, "humidity": 62.0, "rain_probability": 10.0},   # sunny
    {"temperature": 30.0, "humidity": 82.0, "rain_probability": 35.0},   # humid, cloudy
    {"temperature": 28.0, "humidity": 88.0, "rain_probability": 70.0},   # light showers
    {"temperature": 36.0, "humidity": 50.0, "rain_probability": 5.0},    # hot and dry
    {"temperature": 27.0, "humidity": 92.0, "rain_probability": 85.0},   # thunderstorm likely
    {"temperature": 31.0, "humidity": 72.0, "rain_probability": 20.0},   # warm, breezy
]


def sample_weather() -> dict:
    """Offline fallback: a plausible Karaikal weather sample that changes through the day."""
    t = time.localtime()
    return {**_SAMPLES[(t.tm_mday + t.tm_hour) % len(_SAMPLES)], "source": "sample"}


def fetch_weather(lat: float | None = None, lon: float | None = None, fresh: bool = False) -> dict | None:
    """fresh=True skips the 10-minute cache and always asks Open-Meteo."""
    lat = settings.default_lat if lat is None else lat
    lon = settings.default_lon if lon is None else lon
    key = (round(lat, 2), round(lon, 2))
    hit = _CACHE.get(key)
    if not fresh and hit and time.time() - hit[0] < _TTL_S:
        return hit[1]
    query = urllib.parse.urlencode({
        "latitude": lat, "longitude": lon, "timezone": "auto", "forecast_days": 1,
        "current": "temperature_2m,relative_humidity_2m",
        "daily": "precipitation_probability_max",
    })
    try:
        with urllib.request.urlopen(f"https://api.open-meteo.com/v1/forecast?{query}",
                                    timeout=settings.weather_timeout_s) as resp:
            data = json.load(resp)
        out = {
            "temperature": float(data["current"]["temperature_2m"]),
            "humidity": float(data["current"]["relative_humidity_2m"]),
            "rain_probability": float(data["daily"]["precipitation_probability_max"][0] or 0),
            "source": "open-meteo",
        }
    except Exception:
        return sample_weather()
    _CACHE[key] = (time.time(), out)
    return out
