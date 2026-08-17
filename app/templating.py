"""Jinja2 environment shared by the public site and the admin panel."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.security import generate_csrf_token

# Note: the site templates live in templates/site, not templates/public.
# Vercel treats any directory named "public" as static assets and strips it
# from the function bundle, which makes those templates unfindable at runtime.
TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"

templates = Jinja2Templates(directory=str(TEMPLATE_DIR))
templates.env.trim_blocks = True
templates.env.lstrip_blocks = True
templates.env.globals.update(
    site_name=settings.site_name,
    admin_prefix=settings.admin_path_prefix,
    environment=settings.environment,
)


def csrf_token_for(request: Request) -> str:
    """Reuse the cookie token within a request, otherwise mint a new one."""
    token = request.cookies.get(settings.csrf_cookie_name)
    if not token:
        token = getattr(request.state, "csrf_token", None) or generate_csrf_token()
    request.state.csrf_token = token
    return token


def render(
    request: Request,
    template_name: str,
    context: dict[str, Any] | None = None,
    *,
    status_code: int = 200,
    headers: dict[str, str] | None = None,
):
    payload: dict[str, Any] = {"request": request, "csrf_token": csrf_token_for(request)}
    payload.update(context or {})
    response = templates.TemplateResponse(
        request=request,
        name=template_name,
        context=payload,
        status_code=status_code,
        headers=headers,
    )
    if request.cookies.get(settings.csrf_cookie_name) != payload["csrf_token"]:
        response.set_cookie(
            settings.csrf_cookie_name,
            payload["csrf_token"],
            httponly=False,  # readable by the form, compared server-side
            secure=settings.cookie_secure,
            samesite="lax",
            max_age=settings.session_ttl_minutes * 60,
            path="/",
        )
    return response
