"""Agent job queue: enqueue, handler dispatch, failure recording, cron guard."""

from __future__ import annotations

import pytest
from sqlalchemy import select

from app.db.models import AgentJob
from app.db.session import SessionFactory
from app.services import agents


@pytest.mark.asyncio
async def test_enqueue_and_run_registered_handler():
    @agents.handler("test_echo")
    async def _echo(session, payload):
        return {"echoed": payload.get("value")}

    async with SessionFactory() as session:
        job = await agents.enqueue(session, "test_echo", {"value": 42})
        assert job.status == "queued"

        outcomes = await agents.drain(session, limit=10)
        assert any(o["id"] == job.id and o["status"] == "done" for o in outcomes)

        refreshed = await session.get(AgentJob, job.id)
        assert refreshed.result == {"echoed": 42}
        assert refreshed.finished_at is not None


@pytest.mark.asyncio
async def test_unknown_job_type_is_marked_failed():
    async with SessionFactory() as session:
        job = await agents.enqueue(session, "no_such_handler", {})
        await agents.drain(session, limit=10)

        refreshed = await session.get(AgentJob, job.id)
        assert refreshed.status == "failed"
        assert "No handler registered" in refreshed.error


@pytest.mark.asyncio
async def test_handler_error_is_retried_then_failed():
    @agents.handler("test_always_fails")
    async def _boom(session, payload):
        raise RuntimeError("model unavailable")

    async with SessionFactory() as session:
        job = await agents.enqueue(session, "test_always_fails", {})

        for _ in range(3):
            await agents.drain(session, limit=10)

        refreshed = await session.get(AgentJob, job.id)
        assert refreshed.attempts == 3
        assert refreshed.status == "failed"
        assert "model unavailable" in refreshed.error


@pytest.mark.asyncio
async def test_call_claude_requires_key():
    with pytest.raises(agents.AgentNotConfigured):
        await agents.call_claude("hello")


def test_drain_endpoint_requires_configuration(client):
    # CRON_SECRET is unset in tests, so the endpoint refuses to run.
    response = client.post("/api/v1/jobs/drain")
    assert response.status_code == 503
    assert response.json()["ok"] is False


@pytest.mark.asyncio
async def test_queued_jobs_are_processed_in_order():
    async with SessionFactory() as session:
        result = await session.execute(select(AgentJob).where(AgentJob.status == "queued"))
        for stale in result.scalars().all():
            stale.status = "done"
        await session.commit()

        first = await agents.enqueue(session, "test_echo", {"value": 1})
        second = await agents.enqueue(session, "test_echo", {"value": 2})

        outcomes = await agents.drain(session, limit=1)
        assert [o["id"] for o in outcomes] == [first.id]

        outcomes = await agents.drain(session, limit=1)
        assert [o["id"] for o in outcomes] == [second.id]
