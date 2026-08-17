"""Public site and enquiry endpoint."""

from __future__ import annotations


def test_health(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_home_renders_seeded_content(client):
    response = client.get("/")
    assert response.status_code == 200
    body = response.text

    # Sections, projects, experience and ad slots all come from the database.
    assert "Chetan Sharma" in body
    assert "Technical Arsenal" in body
    assert "WhiteLabel Enterprise Web Platform" in body
    assert "Revelex" in body
    assert "TO-LET" in body
    assert "Bucket &amp; Roadmap" in body or "Bucket & Roadmap" in body
    assert "s-maxage" in response.headers["cache-control"]


def test_home_hides_invisible_section(client):
    """Toggling is_visible removes a section from the public page."""
    import asyncio

    from sqlalchemy import select

    from app.db.models import Section
    from app.db.session import SessionFactory

    async def hide(key: str, visible: bool) -> None:
        async with SessionFactory() as session:
            result = await session.execute(select(Section).where(Section.key == key))
            section = result.scalar_one()
            section.is_visible = visible
            await session.commit()

    asyncio.run(hide("adboard", False))
    assert "TO-LET" not in client.get("/").text

    asyncio.run(hide("adboard", True))
    assert "TO-LET" in client.get("/").text


def test_enquiry_is_stored(client):
    payload = {
        "brand": "Acme Cloud",
        "email": "ads@acme.com",
        "budget": 25000,
        "currency": "INR",
        "cycle": "Per month",
        "message": "Q1 campaign, static banner",
        "slot_key": "panel-b",
    }
    response = client.post("/api/v1/enquiries", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["ok"] is True
    # No mail key in tests, so nothing was delivered, but the row must exist.
    assert body["delivered"] is False

    import sqlite3

    from tests.conftest import TEST_DB

    rows = list(
        sqlite3.connect(TEST_DB).execute(
            "select brand, slot_name, budget_amount, mail_sent from enquiries"
        )
    )
    assert ("Acme Cloud", "Panel B", 25000, 0) in rows


def test_enquiry_validation(client):
    bad_cases = [
        {"brand": "", "email": "a@b.com", "budget": 10, "message": "x"},
        {"brand": "A", "email": "not-an-email", "budget": 10, "message": "x"},
        {"brand": "A", "email": "a@b.com", "budget": 0, "message": "x"},
        {"brand": "A", "email": "a@b.com", "budget": 10, "message": ""},
    ]
    for payload in bad_cases:
        assert client.post("/api/v1/enquiries", json=payload).status_code == 422


def test_enquiry_honeypot_rejected(client):
    response = client.post(
        "/api/v1/enquiries",
        json={
            "brand": "Bot",
            "email": "bot@spam.com",
            "budget": 10,
            "message": "spam",
            "company_website": "filled-by-bot",
        },
    )
    assert response.status_code == 400
    assert response.json()["ok"] is False


def test_public_page_is_cacheable(client):
    """A Set-Cookie header would make the page uncacheable at the edge."""
    response = client.get("/")
    assert "set-cookie" not in {k.lower() for k in response.headers}
    assert "s-maxage" in response.headers["cache-control"]


def test_admin_pages_still_issue_csrf_cookie(client):
    response = client.get("/admin/login")
    assert "portfolio_csrf" in response.headers.get("set-cookie", "")


def _set_slot(key: str, **values) -> None:
    """Update an ad slot directly, for rendering tests."""
    import asyncio

    from sqlalchemy import select

    from app.db.models import AdSlot
    from app.db.session import SessionFactory

    async def apply() -> None:
        async with SessionFactory() as session:
            slot = (await session.execute(select(AdSlot).where(AdSlot.key == key))).scalar_one()
            for field, value in values.items():
                setattr(slot, field, value)
            await session.commit()

    asyncio.run(apply())


def test_booked_slot_shows_uploaded_poster(client):
    from app.db.models import AdSlotStatus

    _set_slot(
        "panel-a",
        status=AdSlotStatus.booked,
        brand="Acme Cloud",
        poster_url="https://blob.example/media/acme-poster-1234.png",
        poster_alt="Acme Cloud spring campaign",
        link_url="https://acme.example",
    )
    body = client.get("/").text

    assert 'class="ad-poster"' in body
    assert "https://blob.example/media/acme-poster-1234.png" in body
    assert 'alt="Acme Cloud spring campaign"' in body
    assert 'rel="noopener sponsored"' in body
    assert "Sponsored" in body
    # The poster replaces the placeholder, so this panel no longer advertises itself.
    assert body.count("YOUR AD HERE") == 5

    _set_slot(
        "panel-a",
        status=AdSlotStatus.vacant,
        brand="",
        poster_url="",
        poster_alt="",
        link_url="",
    )
    assert client.get("/").text.count("YOUR AD HERE") == 6


def test_booked_slot_without_poster_uses_logo_layout(client):
    from app.db.models import AdSlotStatus

    _set_slot(
        "panel-b",
        status=AdSlotStatus.booked,
        brand="Beta Tools",
        tagline="Ship faster.",
        logo_url="https://blob.example/media/beta-logo.png",
    )
    body = client.get("/").text

    assert "Beta Tools" in body
    assert "Ship faster." in body
    assert 'class="ad-poster"' not in body
    assert "BOOKED" in body

    _set_slot("panel-b", status=AdSlotStatus.vacant, brand="", tagline="", logo_url="")


def test_poster_alt_falls_back_to_brand(client):
    from app.db.models import AdSlotStatus

    _set_slot(
        "strip-c",
        status=AdSlotStatus.booked,
        brand="Gamma Labs",
        poster_url="https://blob.example/media/gamma.png",
        poster_alt="",
    )
    assert 'alt="Gamma Labs advertisement"' in client.get("/").text

    _set_slot("strip-c", status=AdSlotStatus.vacant, brand="", poster_url="")
