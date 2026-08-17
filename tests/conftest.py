"""Test fixtures: isolated SQLite database per test session, seeded content."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

# Configure the environment before app modules read settings.
TEST_DB = Path(tempfile.gettempdir()) / "portfolio_test.db"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB.as_posix()}"
os.environ["SECRET_KEY"] = "test-secret"
os.environ["ADMIN_PASSWORD"] = "TestPassword123!"
os.environ["ADMIN_EMAIL"] = "admin@example.com"
os.environ["ENVIRONMENT"] = "development"

# Settings also read .env / .env.local, and environment variables win over them.
# Every optional credential is blanked so a value configured on a developer's
# machine (or written there by `vercel env pull`) cannot change a test result.
# Tests that need one of these set it explicitly with monkeypatch.
for optional_secret in (
    "RESEND_API_KEY",
    "CRON_SECRET",
    "ANTHROPIC_API_KEY",
    "BLOB_READ_WRITE_TOKEN",
):
    os.environ[optional_secret] = ""

pytest_plugins = ("pytest_asyncio",)


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session", autouse=True)
def fresh_database():
    if TEST_DB.exists():
        TEST_DB.unlink()

    import asyncio

    from app.seed import run as seed_run

    asyncio.run(seed_run(reset=True))
    yield
    if TEST_DB.exists():
        try:
            TEST_DB.unlink()
        except PermissionError:  # Windows keeps a handle briefly
            pass


@pytest.fixture(autouse=True)
def block_outbound_http(monkeypatch):
    """Fail loudly instead of calling a real API from a test.

    Blanking credentials is not enough on its own: a credential present in a
    developer's .env.local once let a validation test perform a genuine upload
    to the production blob store. Tests that need a response stub
    httpx.AsyncClient.put/post directly, which bypasses send().
    """

    async def refuse(*args, **kwargs):
        raise RuntimeError(
            "Outbound HTTP is blocked in tests. Stub httpx.AsyncClient.put/post instead."
        )

    monkeypatch.setattr("httpx.AsyncClient.send", refuse)


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def admin_client(client):
    """A client with an authenticated admin session cookie."""
    page = client.get("/admin/login")
    csrf = page.cookies.get("portfolio_csrf")
    response = client.post(
        "/admin/login",
        data={
            "email": os.environ["ADMIN_EMAIL"],
            "password": os.environ["ADMIN_PASSWORD"],
            "csrf_token": csrf,
            "next": "",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303, response.text
    client.csrf_token = csrf  # handy for form posts in tests
    return client
