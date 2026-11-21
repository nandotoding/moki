from __future__ import annotations

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request

from backend.app.core.config import APP_NAME, AUTO_CREATE_TABLES, FRONTEND_DIST
from backend.app.core.database import engine
from backend.app.models import Base
from backend.app.routers import auth, transactions, expense_limits, dashboard, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    if AUTO_CREATE_TABLES:
        Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=f"{APP_NAME} API", version="1.2.0", lifespan=lifespan)
app.include_router(auth.router)
app.include_router(transactions.router)
app.include_router(expense_limits.router)
app.include_router(dashboard.router)
app.include_router(admin.router)


@app.get("/api/health", tags=["system"])
def health():
    return {"status": "ok", "app": APP_NAME}


# React is built by Vite into frontend/dist. Recent FastAPI versions provide
# app.frontend(), which Vercel can promote to the CDN. The StaticFiles fallback
# keeps local development compatible with older installed FastAPI versions.
if hasattr(app, "frontend"):
    app.frontend("/", directory=FRONTEND_DIST, fallback="index.html", check_dir=False)
else:
    class SPAStaticFiles(StaticFiles):
        async def get_response(self, path: str, scope):
            try:
                return await super().get_response(path, scope)
            except StarletteHTTPException as exc:
                request = Request(scope)
                accept = request.headers.get("accept", "")
                if request.method in {"GET", "HEAD"} and "text/html" in accept and "." not in path:
                    return await super().get_response("index.html", scope)
                raise exc

    app.mount("/", SPAStaticFiles(directory=FRONTEND_DIST, html=True, check_dir=False), name="frontend")
