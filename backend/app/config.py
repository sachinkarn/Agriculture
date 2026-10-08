"""Runtime settings, read from environment variables (see .env.example)."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]   # .../backend
ROOT_DIR = BASE_DIR.parent                        # project root
_serverless = bool(os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"))
_default_database_path = "/tmp/kisanmitra.db" if _serverless else str(BASE_DIR / "kisanmitra.db")


class Settings:
    database_url: str = os.getenv("DATABASE_URL", f"sqlite:///{_default_database_path}")
    model_dir: Path = Path(os.getenv("MODEL_DIR", BASE_DIR / "models"))
    frontend_dir: Path = Path(os.getenv("FRONTEND_DIR", ROOT_DIR / "frontend"))
    cors_origins: list[str] = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
    max_upload_mb: int = int(os.getenv("MAX_UPLOAD_MB", "8"))
    # Below this top-class probability the API flags the result as "uncertain".
    conf_threshold: float = float(os.getenv("CONF_THRESHOLD", "0.50"))
    # Default location for the weather lookup: Karaikal.
    default_lat: float = float(os.getenv("DEFAULT_LAT", "10.9254"))
    default_lon: float = float(os.getenv("DEFAULT_LON", "79.8380"))
    weather_timeout_s: float = float(os.getenv("WEATHER_TIMEOUT_S", "4"))


settings = Settings()
