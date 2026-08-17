"""Authentication and audit services."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import AuditLog, User, UserRole
from app.security import hash_password, needs_rehash, verify_password


class AuthError(Exception):
    """Raised when a login attempt cannot be completed."""

    def __init__(self, message: str, *, locked: bool = False) -> None:
        super().__init__(message)
        self.message = message
        self.locked = locked


async def record_event(
    session: AsyncSession,
    event: str,
    *,
    detail: str = "",
    actor_email: str = "",
    ip_address: str = "",
    user_id: int | None = None,
) -> None:
    session.add(
        AuditLog(
            event=event,
            detail=detail[:2000],
            actor_email=actor_email[:255],
            ip_address=ip_address[:60],
            user_id=user_id,
        )
    )


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email.lower().strip()))
    return result.scalar_one_or_none()


async def get_user(session: AsyncSession, user_id: int) -> User | None:
    return await session.get(User, user_id)


async def authenticate(
    session: AsyncSession, email: str, password: str, *, ip_address: str = ""
) -> User:
    """Verify credentials, applying lockout after repeated failures."""
    user = await get_user_by_email(session, email)
    now = datetime.now(timezone.utc)

    if user is None:
        await record_event(
            session,
            "login.unknown_user",
            detail=f"No account for {email!r}",
            actor_email=email,
            ip_address=ip_address,
        )
        await session.commit()
        raise AuthError("Email or password is incorrect.")

    if user.locked_until and user.locked_until > now:
        minutes = max(1, int((user.locked_until - now).total_seconds() // 60) + 1)
        raise AuthError(
            f"Account locked after repeated failed attempts. Try again in {minutes} minutes.",
            locked=True,
        )

    if not user.is_active:
        await record_event(
            session,
            "login.inactive",
            actor_email=user.email,
            ip_address=ip_address,
            user_id=user.id,
        )
        await session.commit()
        raise AuthError("This account is disabled.")

    if not verify_password(password, user.password_hash):
        user.failed_login_count += 1
        detail = f"Failed attempt {user.failed_login_count}"
        if user.failed_login_count >= settings.login_max_attempts:
            user.locked_until = now + timedelta(minutes=settings.login_lockout_minutes)
            user.failed_login_count = 0
            detail = f"Locked until {user.locked_until.isoformat()}"
            await record_event(
                session,
                "login.locked",
                detail=detail,
                actor_email=user.email,
                ip_address=ip_address,
                user_id=user.id,
            )
            await session.commit()
            raise AuthError(
                "Too many failed attempts. Account locked for "
                f"{settings.login_lockout_minutes} minutes.",
                locked=True,
            )
        await record_event(
            session,
            "login.failed",
            detail=detail,
            actor_email=user.email,
            ip_address=ip_address,
            user_id=user.id,
        )
        await session.commit()
        raise AuthError("Email or password is incorrect.")

    # Success: reset counters and upgrade the hash if parameters have changed.
    user.failed_login_count = 0
    user.locked_until = None
    user.last_login_at = now
    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)

    await record_event(
        session,
        "login.success",
        actor_email=user.email,
        ip_address=ip_address,
        user_id=user.id,
    )
    await session.commit()
    return user


async def ensure_admin_user(session: AsyncSession, email: str, password: str) -> tuple[User, bool]:
    """Create the bootstrap admin if it does not exist yet."""
    user = await get_user_by_email(session, email)
    if user:
        return user, False

    user = User(
        email=email.lower().strip(),
        full_name=settings.site_name,
        password_hash=hash_password(password),
        role=UserRole.admin,
        is_active=True,
    )
    session.add(user)
    await record_event(session, "user.created", detail="bootstrap admin", actor_email=user.email)
    await session.commit()
    await session.refresh(user)
    return user, True


async def set_password(session: AsyncSession, user: User, new_password: str) -> None:
    user.password_hash = hash_password(new_password)
    user.failed_login_count = 0
    user.locked_until = None
    await record_event(
        session, "user.password_changed", actor_email=user.email, user_id=user.id
    )
    await session.commit()
