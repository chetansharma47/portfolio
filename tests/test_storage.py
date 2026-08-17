"""Image validation and the blob upload path (HTTP calls are stubbed)."""

from __future__ import annotations

import sqlite3

import httpx
import pytest

from app.config import settings
from app.services import storage
from tests.conftest import TEST_DB

PNG_BYTES = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000a49444154789c6300010000050001"
)


# --- validation ------------------------------------------------------------

def test_validate_accepts_png():
    assert storage.validate("logo.png", PNG_BYTES, "image/png") == "image/png"


def test_validate_normalises_content_type_with_charset():
    assert storage.validate("logo.png", PNG_BYTES, "image/png; charset=binary") == "image/png"


def test_validate_rejects_non_image():
    with pytest.raises(storage.UploadRejected, match="Unsupported image type"):
        storage.validate("payload.pdf", b"%PDF-1.4", "application/pdf")


def test_validate_rejects_empty_file():
    with pytest.raises(storage.UploadRejected, match="empty"):
        storage.validate("logo.png", b"", "image/png")


def test_validate_rejects_oversized_file():
    too_big = b"x" * (storage.MAX_UPLOAD_BYTES + 1)
    with pytest.raises(storage.UploadRejected, match="larger than"):
        storage.validate("big.png", too_big, "image/png")


def test_validate_rejects_mismatched_extension():
    with pytest.raises(storage.UploadRejected, match="does not match"):
        storage.validate("script.exe", PNG_BYTES, "image/png")


def test_pathname_is_slugified_and_unguessable():
    first = storage.build_pathname("My Brand Logo!.PNG", "image/png")
    second = storage.build_pathname("My Brand Logo!.PNG", "image/png")
    assert first.startswith("media/my-brand-logo-")
    assert first.endswith(".png")
    assert first != second  # random suffix prevents overwrites


# --- upload ----------------------------------------------------------------

@pytest.mark.asyncio
async def test_upload_requires_token():
    with pytest.raises(storage.StorageNotConfigured):
        await storage.upload_image("logo.png", PNG_BYTES, "image/png")


@pytest.mark.asyncio
async def test_upload_sends_expected_request(monkeypatch):
    captured = {}

    async def fake_put(self, url, content=None, headers=None, **kwargs):
        captured["url"] = url
        captured["headers"] = headers
        captured["size"] = len(content)
        return httpx.Response(
            200,
            json={"url": "https://blob.example/media/logo-abcd1234.png",
                  "pathname": "media/logo-abcd1234.png"},
            request=httpx.Request("PUT", url),
        )

    monkeypatch.setattr(settings, "blob_read_write_token", "test-token")
    monkeypatch.setattr(httpx.AsyncClient, "put", fake_put)

    stored = await storage.upload_image("logo.png", PNG_BYTES, "image/png")

    assert stored.url == "https://blob.example/media/logo-abcd1234.png"
    assert stored.size == len(PNG_BYTES)
    assert captured["headers"]["authorization"] == "Bearer test-token"
    assert captured["headers"]["x-content-type"] == "image/png"
    assert captured["url"].startswith("https://blob.vercel-storage.com/media/logo-")


@pytest.mark.asyncio
async def test_upload_surfaces_provider_error(monkeypatch):
    async def failing_put(self, url, **kwargs):
        return httpx.Response(
            403,
            json={"error": {"message": "Invalid token"}},
            request=httpx.Request("PUT", url),
        )

    monkeypatch.setattr(settings, "blob_read_write_token", "test-token")
    monkeypatch.setattr(httpx.AsyncClient, "put", failing_put)

    with pytest.raises(storage.UploadFailed, match="Invalid token"):
        await storage.upload_image("logo.png", PNG_BYTES, "image/png")


# --- admin integration -----------------------------------------------------

def test_media_library_page(admin_client):
    response = admin_client.get("/admin/media")
    assert response.status_code == 200
    assert "Media library" in response.text
    # No token in the test environment, so uploads must be reported as disabled.
    assert "BLOB_READ_WRITE_TOKEN is not set" in response.text


def test_media_upload_without_file_is_rejected(admin_client):
    response = admin_client.post(
        "/admin/media", data={"csrf_token": admin_client.csrf_token}
    )
    assert response.status_code == 400
    assert "Choose an image file" in response.text


def test_media_upload_stores_asset_and_sets_field(admin_client, monkeypatch):
    async def fake_put(self, url, content=None, headers=None, **kwargs):
        return httpx.Response(
            200,
            json={"url": "https://blob.example/media/profile-99887766.png",
                  "pathname": "media/profile-99887766.png"},
            request=httpx.Request("PUT", url),
        )

    monkeypatch.setattr(settings, "blob_read_write_token", "test-token")
    monkeypatch.setattr(httpx.AsyncClient, "put", fake_put)

    response = admin_client.post(
        "/admin/media",
        data={"csrf_token": admin_client.csrf_token, "alt_text": "Profile photo"},
        files={"image": ("profile.png", PNG_BYTES, "image/png")},
        follow_redirects=False,
    )
    assert response.status_code == 303

    row = sqlite3.connect(TEST_DB).execute(
        "select filename, url, alt_text, used_for from media_assets"
    ).fetchone()
    assert row == (
        "profile.png",
        "https://blob.example/media/profile-99887766.png",
        "Profile photo",
        "library",
    )


def test_image_field_upload_replaces_url(admin_client, monkeypatch):
    async def fake_put(self, url, content=None, headers=None, **kwargs):
        return httpx.Response(
            200,
            json={"url": "https://blob.example/media/hero-11223344.png",
                  "pathname": "media/hero-11223344.png"},
            request=httpx.Request("PUT", url),
        )

    monkeypatch.setattr(settings, "blob_read_write_token", "test-token")
    monkeypatch.setattr(httpx.AsyncClient, "put", fake_put)

    settings_id = sqlite3.connect(TEST_DB).execute(
        "select id from site_settings limit 1"
    ).fetchone()[0]

    response = admin_client.post(
        f"/admin/content/settings/{settings_id}",
        data={
            "csrf_token": admin_client.csrf_token,
            "owner_name": "Chetan Sharma",
            "profile_image": "assets/images/profile.jpg",  # existing value
            "default_theme": "dark",
        },
        files={"profile_image__file": ("newphoto.png", PNG_BYTES, "image/png")},
        follow_redirects=False,
    )
    assert response.status_code == 303

    stored = sqlite3.connect(TEST_DB).execute(
        "select profile_image from site_settings where id = ?", (settings_id,)
    ).fetchone()[0]
    assert stored == "https://blob.example/media/hero-11223344.png"


def test_image_field_keeps_url_when_no_file_uploaded(admin_client):
    settings_id = sqlite3.connect(TEST_DB).execute(
        "select id from site_settings limit 1"
    ).fetchone()[0]

    response = admin_client.post(
        f"/admin/content/settings/{settings_id}",
        data={
            "csrf_token": admin_client.csrf_token,
            "owner_name": "Chetan Sharma",
            "profile_image": "assets/images/profile.jpg",
            "default_theme": "dark",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    stored = sqlite3.connect(TEST_DB).execute(
        "select profile_image from site_settings where id = ?", (settings_id,)
    ).fetchone()[0]
    assert stored == "assets/images/profile.jpg"
