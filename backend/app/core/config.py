from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
APP_NAME = "Moki"
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./moki.db")
APP_ENV = os.getenv("APP_ENV", "development").lower()
COOKIE_SECURE = APP_ENV == "production" or os.getenv("VERCEL") == "1"
COOKIE_NAME = "moki_session"
ADMIN_COOKIE_NAME = "moki_admin_session"
CSRF_COOKIE_NAME = "moki_csrf"
ADMIN_CSRF_COOKIE_NAME = "moki_admin_csrf"
SESSION_DAYS = int(os.getenv("SESSION_DAYS", "30"))
ADMIN_SESSION_HOURS = int(os.getenv("ADMIN_SESSION_HOURS", "12"))
AUTO_CREATE_TABLES = os.getenv("AUTO_CREATE_TABLES", "false").lower() in {"1", "true", "yes"}
FRONTEND_DIST = Path(os.getenv("FRONTEND_DIST", str(BASE_DIR / "frontend" / "dist"))).resolve()
