"""SQLAlchemy setup. SQLite by default, PostgreSQL when DATABASE_URL points to it."""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings

_url = settings.database_url
if _url.startswith("postgres://"):            # some hosts still hand out the old scheme
    _url = _url.replace("postgres://", "postgresql://", 1)

_connect_args = {"check_same_thread": False} if _url.startswith("sqlite") else {}
engine = create_engine(_url, connect_args=_connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
