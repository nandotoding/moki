from __future__ import annotations

from collections.abc import Generator
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from backend.app.core.config import DATABASE_URL


def _normalise_url(raw: str) -> str:
    if raw.startswith("postgres://"):
        return raw.replace("postgres://", "postgresql+psycopg://", 1)
    if raw.startswith("postgresql://"):
        return raw.replace("postgresql://", "postgresql+psycopg://", 1)
    return raw


_url = _normalise_url(DATABASE_URL)
_url_obj = make_url(_url)
_connect_args = {}
_engine_options = {"pool_pre_ping": True}
if _url_obj.drivername.startswith("sqlite"):
    _connect_args["check_same_thread"] = False
    _engine_options["connect_args"] = _connect_args
    _engine_options["pool_size"] = 1
    _engine_options["max_overflow"] = 0
else:
    # Neon pooled endpoints use PgBouncer transaction pooling. Disabling psycopg
    # automatic server-side prepared statements avoids session-state assumptions.
    _connect_args.update({"prepare_threshold": None, "connect_timeout": 10})
    _engine_options.update({
        "connect_args": _connect_args,
        "pool_size": 1,
        "max_overflow": 0,
        "pool_recycle": 300,
        "pool_timeout": 20,
    })

engine = create_engine(_url, **_engine_options)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
