"""Admin panel: login, dashboard, per-entity content control, enquiry inbox."""

from __future__ import annotations

import json
from typing import Annotated, Any

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse, Response
from sqlalchemy import func, select

from app.admin_schema import (
    ENTITY_SPECS,
    REVISION_ENTITY,
    EntitySpec,
    format_field_value,
    parse_form_value,
)
from app.config import settings
from app.db.models import (
    AdSlot,
    AdSlotStatus,
    AuditLog,
    BucketItem,
    ContentRevision,
    Enquiry,
    EnquiryStatus,
    Experience,
    Metric,
    Project,
    Section,
    Skill,
    SkillGroup,
)
from app.dependencies import (
    CsrfGuard,
    CurrentUser,
    EditorUser,
    SessionDep,
    client_ip,
)
from app.security import create_session_token
from app.services import content as content_service
from app.services.auth import AuthError, authenticate, record_event
from app.templating import render

router = APIRouter(prefix=settings.admin_path_prefix, include_in_schema=False)

NO_STORE = {"Cache-Control": "no-store, private", "X-Robots-Tag": "noindex, nofollow"}


def _redirect(path: str) -> RedirectResponse:
    return RedirectResponse(path, status_code=status.HTTP_303_SEE_OTHER)


def _spec_or_404(entity_key: str) -> EntitySpec:
    spec = ENTITY_SPECS.get(entity_key)
    if spec is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown content type")
    return spec


# --- Authentication --------------------------------------------------------

@router.get("/login")
async def login_form(request: Request, next: str = ""):
    return render(
        request,
        "admin/login.html",
        {"next_url": next, "error": None},
        headers=NO_STORE,
    )


@router.post("/login")
async def login_submit(
    request: Request,
    session: SessionDep,
    _csrf: CsrfGuard,
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
    next: Annotated[str, Form()] = "",
):
    try:
        user = await authenticate(session, email, password, ip_address=client_ip(request))
    except AuthError as exc:
        return render(
            request,
            "admin/login.html",
            {"next_url": next, "error": exc.message, "email": email},
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers=NO_STORE,
        )

    target = next if next.startswith(settings.admin_path_prefix) else settings.admin_path_prefix
    response = _redirect(target)
    response.set_cookie(
        settings.session_cookie_name,
        create_session_token(user.id, user.email, user.role.value),
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.session_ttl_minutes * 60,
        path="/",
    )
    return response


@router.post("/logout")
async def logout(request: Request, session: SessionDep, user: CurrentUser, _csrf: CsrfGuard):
    await record_event(
        session, "logout", actor_email=user.email, ip_address=client_ip(request), user_id=user.id
    )
    await session.commit()
    response = _redirect(f"{settings.admin_path_prefix}/login")
    response.delete_cookie(settings.session_cookie_name, path="/")
    return response


# --- Dashboard -------------------------------------------------------------

@router.get("")
async def dashboard(request: Request, session: SessionDep, user: CurrentUser):
    async def count(model) -> int:
        result = await session.execute(select(func.count()).select_from(model))
        return int(result.scalar_one())

    new_enquiries = await session.execute(
        select(func.count()).select_from(Enquiry).where(Enquiry.status == EnquiryStatus.new)
    )
    undelivered = await session.execute(
        select(func.count()).select_from(Enquiry).where(Enquiry.mail_sent.is_(False))
    )
    booked = await session.execute(
        select(func.count()).select_from(AdSlot).where(AdSlot.status == AdSlotStatus.booked)
    )
    recent_enquiries = await session.execute(
        select(Enquiry).order_by(Enquiry.created_at.desc()).limit(5)
    )
    recent_activity = await session.execute(
        select(ContentRevision).order_by(ContentRevision.created_at.desc()).limit(8)
    )
    recent_logins = await session.execute(
        select(AuditLog).order_by(AuditLog.created_at.desc()).limit(6)
    )

    stats = {
        "sections": await count(Section),
        "projects": await count(Project),
        "experience": await count(Experience),
        "skills": await count(Skill),
        "bucket": await count(BucketItem),
        "metrics": await count(Metric),
        "ad_slots": await count(AdSlot),
        "slots_booked": int(booked.scalar_one()),
        "enquiries_new": int(new_enquiries.scalar_one()),
        "enquiries_undelivered": int(undelivered.scalar_one()),
    }

    return render(
        request,
        "admin/dashboard.html",
        {
            "user": user,
            "stats": stats,
            "specs": list(ENTITY_SPECS.values()),
            "recent_enquiries": recent_enquiries.scalars().all(),
            "recent_activity": recent_activity.scalars().all(),
            "recent_logins": recent_logins.scalars().all(),
            "mail_configured": bool(settings.resend_api_key),
        },
        headers=NO_STORE,
    )


# --- Generic entity screens ------------------------------------------------

async def _group_options(session: SessionDep) -> list[tuple[str, str]]:
    result = await session.execute(select(SkillGroup).order_by(SkillGroup.position))
    return [(str(group.id), group.title) for group in result.scalars().all()]


async def _resolve_options(session: SessionDep, spec: EntitySpec) -> dict[str, list[tuple[str, str]]]:
    if spec.key == "skills":
        return {"group_id": await _group_options(session)}
    return {}


@router.get("/content/{entity_key}")
async def entity_list(entity_key: str, request: Request, session: SessionDep, user: CurrentUser):
    spec = _spec_or_404(entity_key)

    if spec.singleton:
        instance = await content_service.get_settings_row(session)
        if instance is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Settings row missing. Run the seed.")
        return _redirect(f"{settings.admin_path_prefix}/content/{entity_key}/{instance.id}")

    order_column = getattr(spec.model, spec.order_by)
    result = await session.execute(select(spec.model).order_by(order_column, spec.model.id))
    rows = result.scalars().all()

    return render(
        request,
        "admin/entity_list.html",
        {
            "user": user,
            "spec": spec,
            "specs": list(ENTITY_SPECS.values()),
            "rows": rows,
            "format_value": format_field_value,
        },
        headers=NO_STORE,
    )


@router.get("/content/{entity_key}/new")
async def entity_new(entity_key: str, request: Request, session: SessionDep, user: EditorUser):
    spec = _spec_or_404(entity_key)
    if spec.singleton:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This record cannot be duplicated.")
    return render(
        request,
        "admin/entity_form.html",
        {
            "user": user,
            "spec": spec,
            "specs": list(ENTITY_SPECS.values()),
            "instance": None,
            "values": {f.name: "" for f in spec.fields},
            "options": await _resolve_options(session, spec),
            "revisions": [],
            "error": None,
        },
        headers=NO_STORE,
    )


@router.get("/content/{entity_key}/{record_id}")
async def entity_edit(
    entity_key: str, record_id: int, request: Request, session: SessionDep, user: CurrentUser
):
    spec = _spec_or_404(entity_key)
    instance = await session.get(spec.model, record_id)
    if instance is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Record not found")

    return render(
        request,
        "admin/entity_form.html",
        {
            "user": user,
            "spec": spec,
            "specs": list(ENTITY_SPECS.values()),
            "instance": instance,
            "values": {
                f.name: format_field_value(f, getattr(instance, f.name, None)) for f in spec.fields
            },
            "options": await _resolve_options(session, spec),
            "revisions": await content_service.revisions_for(
                session, REVISION_ENTITY[entity_key], record_id
            ),
            "error": None,
        },
        headers=NO_STORE,
    )


async def _collect_form_values(request: Request, spec: EntitySpec) -> dict[str, Any]:
    form = await request.form()
    values: dict[str, Any] = {}
    for field_ in spec.fields:
        raw = form.get(field_.name)
        values[field_.name] = parse_form_value(field_, raw if raw is None else str(raw))
    return values


@router.post("/content/{entity_key}/new")
async def entity_create(
    entity_key: str, request: Request, session: SessionDep, user: EditorUser, _csrf: CsrfGuard
):
    spec = _spec_or_404(entity_key)
    try:
        values = await _collect_form_values(request, spec)
    except json.JSONDecodeError as exc:
        return render(
            request,
            "admin/entity_form.html",
            {
                "user": user,
                "spec": spec,
                "specs": list(ENTITY_SPECS.values()),
                "instance": None,
                "values": {f.name: "" for f in spec.fields},
                "options": await _resolve_options(session, spec),
                "revisions": [],
                "error": f"JSON field is invalid: {exc.msg}",
            },
            status_code=status.HTTP_400_BAD_REQUEST,
            headers=NO_STORE,
        )

    instance = await content_service.create_instance(
        session, spec.model, values, entity=REVISION_ENTITY[entity_key], user_id=user.id
    )
    return _redirect(f"{settings.admin_path_prefix}/content/{entity_key}/{instance.id}?saved=1")


@router.post("/content/{entity_key}/{record_id}")
async def entity_update(
    entity_key: str,
    record_id: int,
    request: Request,
    session: SessionDep,
    user: EditorUser,
    _csrf: CsrfGuard,
):
    spec = _spec_or_404(entity_key)
    instance = await session.get(spec.model, record_id)
    if instance is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Record not found")

    try:
        values = await _collect_form_values(request, spec)
    except json.JSONDecodeError as exc:
        return render(
            request,
            "admin/entity_form.html",
            {
                "user": user,
                "spec": spec,
                "specs": list(ENTITY_SPECS.values()),
                "instance": instance,
                "values": {
                    f.name: format_field_value(f, getattr(instance, f.name, None))
                    for f in spec.fields
                },
                "options": await _resolve_options(session, spec),
                "revisions": await content_service.revisions_for(
                    session, REVISION_ENTITY[entity_key], record_id
                ),
                "error": f"JSON field is invalid: {exc.msg}",
            },
            status_code=status.HTTP_400_BAD_REQUEST,
            headers=NO_STORE,
        )

    await content_service.apply_update(
        session, instance, values, entity=REVISION_ENTITY[entity_key], user_id=user.id
    )
    return _redirect(f"{settings.admin_path_prefix}/content/{entity_key}/{record_id}?saved=1")


@router.post("/content/{entity_key}/{record_id}/delete")
async def entity_delete(
    entity_key: str,
    record_id: int,
    request: Request,
    session: SessionDep,
    user: EditorUser,
    _csrf: CsrfGuard,
):
    spec = _spec_or_404(entity_key)
    if spec.singleton:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This record cannot be deleted.")
    instance = await session.get(spec.model, record_id)
    if instance is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Record not found")

    await content_service.delete_instance(
        session, instance, entity=REVISION_ENTITY[entity_key], user_id=user.id
    )
    return _redirect(f"{settings.admin_path_prefix}/content/{entity_key}?deleted=1")


@router.post("/content/{entity_key}/{record_id}/rollback/{version}")
async def entity_rollback(
    entity_key: str,
    record_id: int,
    version: int,
    request: Request,
    session: SessionDep,
    user: EditorUser,
    _csrf: CsrfGuard,
):
    _spec_or_404(entity_key)
    result = await session.execute(
        select(ContentRevision).where(
            ContentRevision.entity == REVISION_ENTITY[entity_key],
            ContentRevision.entity_id == record_id,
            ContentRevision.version == version,
        )
    )
    revision = result.scalar_one_or_none()
    if revision is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Revision not found")

    restored = await content_service.rollback_to(session, revision, user_id=user.id)
    if restored is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This revision cannot be restored.")
    return _redirect(
        f"{settings.admin_path_prefix}/content/{entity_key}/{record_id}?rolledback={version}"
    )


# --- Enquiry inbox ---------------------------------------------------------

@router.get("/enquiries")
async def enquiry_inbox(
    request: Request, session: SessionDep, user: CurrentUser, status_filter: str = ""
):
    stmt = select(Enquiry).order_by(Enquiry.created_at.desc()).limit(200)
    if status_filter:
        try:
            stmt = stmt.where(Enquiry.status == EnquiryStatus(status_filter))
        except ValueError:
            pass
    result = await session.execute(stmt)
    return render(
        request,
        "admin/enquiries.html",
        {
            "user": user,
            "specs": list(ENTITY_SPECS.values()),
            "enquiries": result.scalars().all(),
            "statuses": [s.value for s in EnquiryStatus],
            "status_filter": status_filter,
        },
        headers=NO_STORE,
    )


@router.post("/enquiries/{enquiry_id}")
async def enquiry_update(
    enquiry_id: int,
    request: Request,
    session: SessionDep,
    user: EditorUser,
    _csrf: CsrfGuard,
    new_status: Annotated[str, Form()] = "",
    admin_notes: Annotated[str, Form()] = "",
):
    enquiry = await session.get(Enquiry, enquiry_id)
    if enquiry is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Enquiry not found")

    if new_status:
        try:
            enquiry.status = EnquiryStatus(new_status)
        except ValueError:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown status") from None
    enquiry.admin_notes = admin_notes[:4000]

    await record_event(
        session,
        "enquiry.updated",
        detail=f"#{enquiry.id} -> {enquiry.status.value}",
        actor_email=user.email,
        ip_address=client_ip(request),
        user_id=user.id,
    )
    await session.commit()
    return _redirect(f"{settings.admin_path_prefix}/enquiries")


# --- Activity log ----------------------------------------------------------

@router.get("/activity")
async def activity(request: Request, session: SessionDep, user: CurrentUser):
    revisions = await session.execute(
        select(ContentRevision).order_by(ContentRevision.created_at.desc()).limit(100)
    )
    events = await session.execute(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(100))
    return render(
        request,
        "admin/activity.html",
        {
            "user": user,
            "specs": list(ENTITY_SPECS.values()),
            "revisions": revisions.scalars().all(),
            "events": events.scalars().all(),
        },
        headers=NO_STORE,
    )
