"""FastAPI application factory."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.dependencies import LoginRequired, redirect_to_login
from app.routers import admin, public
from app.templating import render

logging.basicConfig(level=logging.INFO if not settings.debug else logging.DEBUG)
logger = logging.getLogger("portfolio")

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("starting portfolio app env=%s", settings.environment)
    yield
    from app.db.session import engine

    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Portfolio CMS",
        version="2.0.0",
        docs_url="/api/docs" if settings.debug else None,
        redoc_url=None,
        openapi_url="/api/openapi.json" if settings.debug else None,
        lifespan=lifespan,
    )

    app.include_router(admin.router)
    app.include_router(public.router)

    # In production Vercel serves /assets from its CDN; this mount is for local dev.
    if ASSETS_DIR.exists():
        app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")

    @app.exception_handler(LoginRequired)
    async def login_required_handler(request: Request, exc: LoginRequired):
        return redirect_to_login(exc.next_url)

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        if request.url.path.startswith(settings.admin_path_prefix):
            response.headers["Cache-Control"] = "no-store, private"
            response.headers["X-Robots-Tag"] = "noindex, nofollow"
        return response

    @app.exception_handler(404)
    async def not_found(request: Request, exc):
        if request.url.path.startswith("/api/"):
            return JSONResponse({"ok": False, "error": "Not found"}, status_code=404)
        return render(request, "public/404.html", {}, status_code=404)

    return app


app = create_app()
