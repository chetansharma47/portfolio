"""Agent and AI job layer.

Serverless requests are short lived, so anything that calls a model runs as a
queued job rather than inside a page request:

    enqueue(session, "draft_section_copy", {"section_key": "hero"})

A scheduled request to /api/v1/jobs/drain (Vercel Cron) picks jobs up, runs the
handler registered for the job type and stores the result. Handlers are plain
async functions, so they are callable from tests without HTTP or a scheduler.

The only handler shipped today drafts alternative section copy with Claude and
stores it as a suggestion; it never writes to live content on its own.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import AgentJob, Section

logger = logging.getLogger("portfolio.agents")

ANTHROPIC_ENDPOINT = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"

JobHandler = Callable[[AsyncSession, dict[str, Any]], Awaitable[dict[str, Any]]]
HANDLERS: dict[str, JobHandler] = {}


class AgentNotConfigured(RuntimeError):
    pass


def handler(job_type: str) -> Callable[[JobHandler], JobHandler]:
    def register(func: JobHandler) -> JobHandler:
        HANDLERS[job_type] = func
        return func

    return register


async def enqueue(
    session: AsyncSession,
    job_type: str,
    payload: dict[str, Any] | None = None,
    *,
    commit: bool = True,
) -> AgentJob:
    job = AgentJob(job_type=job_type, payload=payload or {}, status="queued")
    session.add(job)
    if commit:
        await session.commit()
        await session.refresh(job)
    return job


async def call_claude(prompt: str, *, system: str = "", max_tokens: int = 1024) -> str:
    """Single-turn call to the Messages API. Raises if no key is configured."""
    if not settings.anthropic_api_key:
        raise AgentNotConfigured("ANTHROPIC_API_KEY is not set")

    body: dict[str, Any] = {
        "model": settings.agent_model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        body["system"] = system

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            ANTHROPIC_ENDPOINT,
            headers={
                "x-api-key": settings.anthropic_api_key,
                "anthropic-version": ANTHROPIC_VERSION,
                "content-type": "application/json",
            },
            json=body,
        )

    if response.status_code >= 400:
        raise RuntimeError(f"Model call failed ({response.status_code}): {response.text[:300]}")

    data = response.json()
    parts = [block.get("text", "") for block in data.get("content", []) if block.get("type") == "text"]
    return "".join(parts).strip()


@handler("draft_section_copy")
async def draft_section_copy(session: AsyncSession, payload: dict[str, Any]) -> dict[str, Any]:
    """Draft an alternative version of a section's copy as a suggestion."""
    section_key = payload.get("section_key", "")
    result = await session.execute(select(Section).where(Section.key == section_key))
    section = result.scalar_one_or_none()
    if section is None:
        raise ValueError(f"Unknown section: {section_key!r}")

    draft = await call_claude(
        prompt=(
            "Rewrite this portfolio section copy. Keep the facts identical, keep it plain and "
            "professional, no marketing superlatives, British spelling.\n\n"
            f"Heading: {section.heading}\n\nBody: {section.subheading}"
        ),
        system="You are editing a working engineer's portfolio. Never invent achievements.",
        max_tokens=800,
    )
    return {"section_key": section_key, "suggestion": draft}


async def run_job(session: AsyncSession, job: AgentJob) -> AgentJob:
    job_handler = HANDLERS.get(job.job_type)
    job.attempts += 1
    job.started_at = datetime.now(timezone.utc)

    if job_handler is None:
        job.status = "failed"
        job.error = f"No handler registered for {job.job_type!r}"
        job.finished_at = datetime.now(timezone.utc)
        await session.commit()
        return job

    try:
        job.result = await job_handler(session, job.payload or {})
        job.status = "done"
        job.error = ""
    except Exception as exc:  # noqa: BLE001 - recorded on the job row
        logger.exception("agent job %s failed", job.id)
        job.status = "failed" if job.attempts >= 3 else "queued"
        job.error = str(exc)[:2000]

    job.finished_at = datetime.now(timezone.utc)
    await session.commit()
    return job


async def drain(session: AsyncSession, limit: int = 5) -> list[dict[str, Any]]:
    """Run up to `limit` queued jobs. Called by the scheduled endpoint."""
    result = await session.execute(
        select(AgentJob).where(AgentJob.status == "queued").order_by(AgentJob.id).limit(limit)
    )
    jobs = list(result.scalars().all())

    outcomes = []
    for job in jobs:
        await run_job(session, job)
        outcomes.append({"id": job.id, "type": job.job_type, "status": job.status, "error": job.error})
    return outcomes
