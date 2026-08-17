# Portfolio Platform — Chetan Sharma

A content-managed portfolio: a public server-rendered site and a private admin
console, one FastAPI application, deployed on Vercel.

- **Public site** — `/` — server-rendered from the database, so search engines
  see the full content and there is no empty-then-populate flash.
- **Admin console** — `/admin` — every section, project, role, skill, bucket
  item and ad slot is editable, with revision history and rollback.

## Stack

| Layer | Choice | Why |
| --- | --- | --- |
| Web framework | FastAPI (ASGI, Python 3.12) | async, typed, first-class for AI/agent libraries |
| Templating | Jinja2 | server-rendered pages, no build step |
| Database | Postgres (Neon) via SQLAlchemy 2.0 async + asyncpg | serverless-friendly pooling, `pgvector` available for future RAG |
| Migrations | Alembic | reviewable schema history |
| Auth | Argon2 hashes, JWT session in an httpOnly cookie, CSRF double-submit | no shared session store needed on serverless |
| Mail | Resend REST API | key stays server-side |
| Analytics | Vercel Web Analytics | page views plus custom events |
| Hosting | Vercel Python runtime (`api/index.py`) | same platform as before |
| Tests | pytest + FastAPI TestClient over SQLite | fast, no external services |

## Layout

```
api/index.py            Vercel entry point exposing the ASGI app
app/
  config.py             settings from environment variables
  main.py               app factory, middleware, error handlers
  security.py           password hashing, session tokens, CSRF
  dependencies.py       current user, role guards, CSRF guard
  admin_schema.py       declarative admin form definitions
  db/
    base.py             declarative base, timestamp mixin
    session.py          async engine (NullPool on serverless)
    models.py           all tables
  routers/
    public.py           SSR pages, enquiry API, cron job drain
    admin.py            login, dashboard, content CRUD, enquiry inbox
  services/
    auth.py             authentication, lockout, audit events
    content.py          content reads plus writes with revision history
    mail.py             Resend delivery
    agents.py           AI job queue, handlers, Claude calls
  templates/            public/ and admin/ Jinja2 templates
  seed_data.py          the original portfolio content
  seed.py               idempotent seeding CLI
alembic/                migration environment and versions
assets/                 CSS, JS and images served straight from the CDN
tests/                  pytest suite
```

## Local development

```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements-dev.txt

copy .env.example .env.local        # then fill in the values

.venv\Scripts\python -m alembic upgrade head
.venv\Scripts\python -m app.seed    # inserts the starting content + admin user
.venv\Scripts\python -m uvicorn app.main:app --reload
```

Public site on http://127.0.0.1:8000, console on http://127.0.0.1:8000/admin.

Without `DATABASE_URL` the app falls back to a local SQLite file, which is how
the tests run. Point `DATABASE_URL` at Neon to develop against Postgres.

`python -m app.seed` is safe to re-run: it only inserts records that are
missing and never overwrites content edited in the console. `--reset` drops
everything first and is refused when `ENVIRONMENT=production`.

If `ADMIN_PASSWORD` is not set, the seed generates one and prints it once.

## Tests

```bash
.venv\Scripts\python -m pytest
```

Covers the public page, section visibility, enquiry validation and storage,
login failures and lockout auditing, CSRF rejection, content create/edit/delete,
revision rollback, the enquiry inbox and the agent job queue.

## Environment variables

| Variable | Required | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | production | Neon Postgres URL (pooled endpoint) |
| `SECRET_KEY` | production | signs admin session cookies |
| `ADMIN_EMAIL` | seed | bootstrap admin account |
| `ADMIN_PASSWORD` | seed | bootstrap password; generated if absent |
| `RESEND_API_KEY` | for mail | enquiry notifications |
| `ENQUIRY_TO` / `ENQUIRY_FROM` | no | override recipient/sender |
| `BLOB_READ_WRITE_TOKEN` | for uploads | set automatically by the Vercel Blob store |
| `ANTHROPIC_API_KEY` | for agents | model calls from queued jobs |
| `CRON_SECRET` | for agents | required by `/api/v1/jobs/drain` |
| `ENVIRONMENT` | no | `development` / `preview` / `production` |
| `PUBLIC_CACHE_SECONDS` | no | edge cache lifetime for public pages |

`postgres://` and `postgresql://` URLs are rewritten to the asyncpg driver
automatically, and libpq-only query parameters such as `sslmode` are stripped.

## Deployment (Vercel)

1. Add the environment variables above under **Project → Settings →
   Environment Variables**.
2. Create the Neon database and run migrations against it:
   `DATABASE_URL=... .venv\Scripts\python -m alembic upgrade head`
   then `DATABASE_URL=... .venv\Scripts\python -m app.seed`.
3. Push. `vercel.json` rewrites everything except `/assets` and `/_vercel` to
   `api/index.py`, so the ASGI app serves both surfaces.

Serverless constraints that shaped the design:

- No persistent filesystem, so image uploads go to Vercel Blob rather than
  local disk (see Media below).
- Request duration is capped, so model calls run as queued jobs drained by the
  daily cron rather than inside a page request.
- Connections use `NullPool` in production; the Neon pooler owns pooling.

## Content model notes

- **Sections** hold heading, intro copy, ordering, visibility and a small JSON
  `body` for section-specific extras (hero buttons, board marquee, CTA text).
- **Typed tables** back the repeated content: metrics, skill groups + skills,
  projects, experience, bucket items, ad slots.
- **Every write** records a `content_revisions` row with the full before/after
  payload, shown in the form sidebar and restorable in one click.
- **Security events** (logins, failures, lockouts, deletions) land in
  `audit_logs`, visible under **Activity log**.

## Media

Images are uploaded to a public Vercel Blob store, created once with:

```bash
vercel blob create-store portfolio-media --access public --yes
```

That writes `BLOB_READ_WRITE_TOKEN` into every environment. Uploads are
validated before leaving the process (PNG, JPEG, WebP, GIF, SVG, AVIF, 4 MB
limit, extension must match the content type) and stored under a pathname with a
random suffix, so an upload can neither overwrite another nor be guessed.

Two ways in:

- **Media library** (`/admin/media`) — upload, copy the URL, delete. Deleting
  removes the blob as well as the row, and is recorded in the audit log.
- **Image fields** on a content form (profile image, ad slot poster and logo) —
  choose a file to replace the current one, or paste a URL. Every upload is also
  recorded in `media_assets`.

### Running a campaign on the ad board

Set the slot's status to `booked`, upload the advertiser's finished creative as
the **advertisement poster**, add alt text and the click-through link. The poster
fills the whole panel and carries a "Sponsored" label; outbound links use
`rel="noopener sponsored"`. The logo plus tagline layout is the fallback used
only when no poster has been uploaded.

`app/services/storage.py` talks to the Blob HTTP API directly; there is no
official Python SDK.

## Agent extension point

`app/services/agents.py` registers async handlers by job type:

```python
@handler("draft_section_copy")
async def draft_section_copy(session, payload): ...
```

Enqueue with `await enqueue(session, "draft_section_copy", {"section_key": "hero"})`.
The daily cron drains the queue, records results and retries a failing job up to
three times. The shipped handler drafts alternative copy and stores it as a
suggestion; it never edits live content by itself.
