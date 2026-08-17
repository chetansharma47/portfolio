"""Public site: server-rendered pages plus the enquiry endpoint."""

from __future__ import annotations

import re
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field, field_validator

from app.config import settings
from app.db.models import AdSlot, Enquiry
from app.dependencies import SessionDep, client_ip, user_agent
from app.services import content as content_service
from app.services.mail import EnquiryMail, MailNotConfigured, MailSendFailed, send_enquiry
from app.templating import render

router = APIRouter()

CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")


def _clean(value: str, limit: int) -> str:
    return CONTROL_CHARS.sub(" ", value or "").strip()[:limit]


class EnquiryIn(BaseModel):
    brand: str = Field(min_length=1, max_length=60)
    email: EmailStr
    budget: int = Field(gt=0, le=100_000_000)
    currency: str = Field(default="INR", max_length=8)
    cycle: str = Field(default="Per month", max_length=40)
    message: str = Field(min_length=1, max_length=400)
    slot_key: str = Field(default="", max_length=60)
    company_website: str = Field(default="", max_length=100)  # honeypot

    @field_validator("brand", "message", "currency", "cycle", "slot_key")
    @classmethod
    def strip_control_chars(cls, value: str) -> str:
        return _clean(value, 400)


@router.get("/healthz", include_in_schema=False)
async def healthz(session: SessionDep) -> dict[str, str]:
    from sqlalchemy import text

    await session.execute(text("SELECT 1"))
    return {"status": "ok", "environment": settings.environment}


def _build_site_data(context: dict) -> dict:
    """Small JSON payload the front-end script needs (CLI content, contacts)."""
    settings_row = context.get("settings_row")
    return {
        "owner": settings_row.owner_name if settings_row else settings.site_name,
        "email": settings_row.email if settings_row else "",
        "phone": settings_row.phone if settings_row else "",
        "location": settings_row.location if settings_row else "",
        "linkedin": settings_row.linkedin_url if settings_row else "",
        "defaultTheme": settings_row.default_theme if settings_row else "dark",
        "projects": [
            {"title": p.title, "badge": p.badge, "link": p.link_url} for p in context["projects"]
        ],
        "experience": [
            {"role": e.role, "company": e.company, "period": e.period}
            for e in context["experiences"]
        ],
        "skills": [
            {"group": g.title, "items": [s.name for s in g.skills]}
            for g in context["skill_groups"]
        ],
        "bucket": [
            {"title": b.title, "type": b.item_type.value, "progress": b.progress, "target": b.target}
            for b in context["bucket_items"]
        ],
        "adSlots": [
            {"key": s.key, "name": s.name, "size": s.size, "status": s.status.value}
            for s in context["ad_slots"]
        ],
    }


@router.get("/", response_class=Response)
async def home(request: Request, session: SessionDep):
    context = await content_service.public_page_context(session)
    context["bucket_stats"] = content_service.bucket_stats(context["bucket_items"])
    context["site_data"] = _build_site_data(context)
    headers = {
        "Cache-Control": (
            f"public, max-age=0, s-maxage={settings.public_cache_seconds}, "
            "stale-while-revalidate=300"
        )
    }
    return render(request, "public/index.html", context, headers=headers)


@router.api_route("/api/v1/jobs/drain", methods=["GET", "POST"], include_in_schema=False)
async def drain_jobs(request: Request, session: SessionDep) -> JSONResponse:
    """Run queued agent jobs.

    Vercel Cron issues a GET with `Authorization: Bearer $CRON_SECRET`, so both
    verbs are accepted and the secret is always required.
    """
    from app.services.agents import drain

    if not settings.cron_secret:
        return JSONResponse({"ok": False, "error": "Scheduler is not configured."}, status_code=503)

    provided = request.headers.get("authorization", "").removeprefix("Bearer ").strip()
    if provided != settings.cron_secret:
        return JSONResponse({"ok": False, "error": "Unauthorised."}, status_code=401)

    outcomes = await drain(session, limit=settings.job_batch_size)
    return JSONResponse({"ok": True, "processed": len(outcomes), "jobs": outcomes})


@router.post("/api/v1/enquiries", status_code=status.HTTP_201_CREATED)
async def create_enquiry(
    payload: EnquiryIn,
    request: Request,
    session: SessionDep,
) -> JSONResponse:
    """Store the enquiry, then notify by mail. Storage is the source of truth."""
    if payload.company_website:
        return JSONResponse({"ok": False, "error": "Submission rejected."}, status_code=400)

    slot: AdSlot | None = None
    if payload.slot_key:
        from sqlalchemy import select

        result = await session.execute(select(AdSlot).where(AdSlot.key == payload.slot_key))
        slot = result.scalar_one_or_none()

    enquiry = Enquiry(
        slot_key=payload.slot_key,
        slot_name=slot.name if slot else "Portfolio Board",
        brand=payload.brand,
        email=str(payload.email),
        budget_amount=payload.budget,
        currency=payload.currency.upper(),
        billing_cycle=payload.cycle,
        message=payload.message,
        source_ip=client_ip(request),
        user_agent=user_agent(request),
    )
    session.add(enquiry)
    await session.commit()
    await session.refresh(enquiry)

    mail = EnquiryMail(
        brand=enquiry.brand,
        email=enquiry.email,
        budget_amount=enquiry.budget_amount,
        currency=enquiry.currency,
        billing_cycle=enquiry.billing_cycle,
        message=enquiry.message,
        slot_name=enquiry.slot_name,
        slot_size=slot.size if slot else "",
        placement=slot.placement if slot else "",
    )

    try:
        await send_enquiry(mail)
        enquiry.mail_sent = True
    except (MailNotConfigured, MailSendFailed) as exc:
        enquiry.mail_error = str(exc)[:2000]
    await session.commit()

    # The enquiry is saved either way, so the visitor always sees success.
    return JSONResponse(
        {"ok": True, "id": enquiry.id, "delivered": enquiry.mail_sent},
        status_code=status.HTTP_201_CREATED,
    )
