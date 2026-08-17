"""Shared FastAPI dependencies: current user, CSRF guard, client metadata."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import User, UserRole
from app.db.session import get_session
from app.security import csrf_tokens_match, decode_session_token
from app.services.auth import get_user

SessionDep = Annotated[AsyncSession, Depends(get_session)]


class LoginRequired(HTTPException):
    """Signals the admin login redirect; handled by an exception handler."""

    def __init__(self, next_url: str = "") -> None:
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login required")
        self.next_url = next_url


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()[:60]
    return (request.client.host if request.client else "")[:60]


def user_agent(request: Request) -> str:
    return request.headers.get("user-agent", "")[:255]


async def optional_user(request: Request, session: SessionDep) -> User | None:
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        return None
    claims = decode_session_token(token)
    if not claims:
        return None
    try:
        user_id = int(claims.get("sub", ""))
    except (TypeError, ValueError):
        return None
    user = await get_user(session, user_id)
    if user is None or not user.is_active:
        return None
    return user


async def current_user(
    request: Request, user: Annotated[User | None, Depends(optional_user)]
) -> User:
    if user is None:
        raise LoginRequired(next_url=str(request.url.path))
    return user


async def require_editor(user: Annotated[User, Depends(current_user)]) -> User:
    if user.role == UserRole.viewer:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This account has read-only access.")
    return user


async def require_admin(user: Annotated[User, Depends(current_user)]) -> User:
    if user.role != UserRole.admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Administrator access required.")
    return user


async def verify_csrf(request: Request, csrf_token: Annotated[str, Form()] = "") -> None:
    cookie_token = request.cookies.get(settings.csrf_cookie_name)
    if not csrf_tokens_match(cookie_token, csrf_token):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Invalid or expired form token.")


CurrentUser = Annotated[User, Depends(current_user)]
EditorUser = Annotated[User, Depends(require_editor)]
AdminUser = Annotated[User, Depends(require_admin)]
CsrfGuard = Annotated[None, Depends(verify_csrf)]


def redirect_to_login(next_url: str = "") -> RedirectResponse:
    target = f"{settings.admin_path_prefix}/login"
    if next_url:
        target = f"{target}?next={next_url}"
    return RedirectResponse(target, status_code=status.HTTP_303_SEE_OTHER)
