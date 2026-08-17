"""Image uploads to Vercel Blob.

Serverless functions have no writable disk, so uploads go straight to Vercel
Blob over its HTTP API (there is no official Python SDK). Files are validated
by content type, extension and size before anything leaves the process, and the
stored pathname carries a random suffix so one upload can never overwrite
another or be guessed from the original filename.
"""

from __future__ import annotations

import re
import secrets
from dataclasses import dataclass

import httpx

from app.config import settings

BLOB_API = "https://blob.vercel-storage.com"
BLOB_API_VERSION = "7"

MAX_UPLOAD_BYTES = 4 * 1024 * 1024  # 4 MB: comfortably under the request limit

ALLOWED_TYPES = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "image/svg+xml": ".svg",
    "image/avif": ".avif",
}

SLUG_PATTERN = re.compile(r"[^a-z0-9]+")


class StorageNotConfigured(RuntimeError):
    pass


class UploadRejected(ValueError):
    """The file failed validation; the message is safe to show a user."""


class UploadFailed(RuntimeError):
    pass


@dataclass(slots=True)
class StoredImage:
    url: str
    pathname: str
    size: int
    content_type: str


def _slugify(value: str, limit: int = 40) -> str:
    stem = value.rsplit(".", 1)[0].lower()
    slug = SLUG_PATTERN.sub("-", stem).strip("-")
    return (slug or "image")[:limit]


def build_pathname(filename: str, content_type: str, *, folder: str = "media") -> str:
    extension = ALLOWED_TYPES[content_type]
    return f"{folder}/{_slugify(filename)}-{secrets.token_hex(4)}{extension}"


def validate(filename: str, content: bytes, content_type: str) -> str:
    """Return the normalised content type, or raise UploadRejected."""
    normalised = (content_type or "").split(";")[0].strip().lower()

    if normalised not in ALLOWED_TYPES:
        allowed = ", ".join(sorted(t.split("/")[-1] for t in ALLOWED_TYPES))
        raise UploadRejected(f"Unsupported image type. Allowed: {allowed}.")

    if not content:
        raise UploadRejected("The file is empty.")

    if len(content) > MAX_UPLOAD_BYTES:
        limit_mb = MAX_UPLOAD_BYTES // (1024 * 1024)
        raise UploadRejected(f"File is larger than {limit_mb} MB.")

    extension = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension and extension not in ALLOWED_TYPES.values() and extension != ".jpeg":
        raise UploadRejected(f"Extension {extension} does not match an allowed image type.")

    return normalised


async def upload_image(
    filename: str, content: bytes, content_type: str, *, folder: str = "media"
) -> StoredImage:
    if not settings.blob_read_write_token:
        raise StorageNotConfigured("BLOB_READ_WRITE_TOKEN is not set")

    normalised = validate(filename, content, content_type)
    pathname = build_pathname(filename, normalised, folder=folder)

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.put(
                f"{BLOB_API}/{pathname}",
                content=content,
                headers={
                    "authorization": f"Bearer {settings.blob_read_write_token}",
                    "x-api-version": BLOB_API_VERSION,
                    "x-content-type": normalised,
                    # Pathnames already carry a random suffix, so no extra suffix.
                    "x-add-random-suffix": "0",
                    "x-cache-control-max-age": "31536000",
                },
            )
        except httpx.HTTPError as exc:
            raise UploadFailed(f"Blob storage unreachable: {exc}") from exc

    if response.status_code >= 400:
        detail = ""
        try:
            detail = response.json().get("error", {}).get("message", "")
        except ValueError:
            detail = response.text[:200]
        raise UploadFailed(detail or f"Blob storage returned {response.status_code}")

    payload = response.json()
    return StoredImage(
        url=payload.get("url", ""),
        pathname=payload.get("pathname", pathname),
        size=len(content),
        content_type=normalised,
    )


async def delete_blob(url: str) -> bool:
    """Remove a blob. Returns False when storage is not configured."""
    if not settings.blob_read_write_token:
        return False

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BLOB_API}/delete",
            json={"urls": [url]},
            headers={
                "authorization": f"Bearer {settings.blob_read_write_token}",
                "x-api-version": BLOB_API_VERSION,
            },
        )
    return response.status_code < 400
