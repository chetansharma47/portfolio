#!/usr/bin/env bash
# Configure the Vercel project from .env.local, then migrate and seed the database.
#
#   bash scripts/setup_vercel.sh
#
# Prerequisites (the only steps that need a human):
#   1. vercel login
#   2. A Postgres database attached to the project, either through
#      Vercel -> Storage -> Neon, or by putting DATABASE_URL in .env.local.
#
# Safe to re-run: existing variables are updated, and the seed only inserts
# records that are missing.

set -euo pipefail

cd "$(dirname "$0")/.."

PY=".venv/Scripts/python.exe"
[ -x "$PY" ] || PY="python"

ENV_FILE=".env.local"
ENVIRONMENTS=("production" "preview" "development")
# Variables pushed to Vercel. DATABASE_URL is deliberately absent: the Neon
# integration manages it, and a hand-set value would shadow the managed one.
KEYS=(SECRET_KEY ADMIN_EMAIL ADMIN_PASSWORD RESEND_API_KEY ENQUIRY_TO ENQUIRY_FROM CRON_SECRET)

read_env() {
  # read_env KEY -> value from .env.local. Quotes are stripped because
  # `vercel env pull` and `vercel blob create-store` rewrite the file quoted.
  sed -n "s/^$1=//p" "$ENV_FILE" | head -1 | sed 's/^"//; s/"$//'
}

step() { printf '\n=== %s ===\n' "$1"; }

step "Checking Vercel authentication"
if ! vercel whoami >/dev/null 2>&1; then
  echo "Not logged in. Run: vercel login" >&2
  exit 1
fi
echo "Logged in as: $(vercel whoami 2>/dev/null | tail -1)"

step "Linking the project"
if [ -d ".vercel" ]; then
  echo "Already linked."
else
  vercel link --yes
fi

step "Setting environment variables"
for key in "${KEYS[@]}"; do
  value="$(read_env "$key" || true)"
  if [ -z "$value" ]; then
    echo "  skip $key (not in $ENV_FILE)"
    continue
  fi
  for environment in "${ENVIRONMENTS[@]}"; do
    # remove-then-add, because `env add` refuses to overwrite
    vercel env rm "$key" "$environment" --yes >/dev/null 2>&1 || true
    printf '%s' "$value" | vercel env add "$key" "$environment" >/dev/null 2>&1 \
      && echo "  set $key ($environment)" \
      || echo "  FAILED $key ($environment)" >&2
  done
done

# ENVIRONMENT is per-environment rather than copied from .env.local.
for environment in "${ENVIRONMENTS[@]}"; do
  case "$environment" in
    production) value="production" ;;
    preview) value="preview" ;;
    *) value="development" ;;
  esac
  vercel env rm ENVIRONMENT "$environment" --yes >/dev/null 2>&1 || true
  printf '%s' "$value" | vercel env add ENVIRONMENT "$environment" >/dev/null 2>&1 \
    && echo "  set ENVIRONMENT=$value ($environment)"
done

step "Pulling the resolved variables back"
vercel env pull .env.vercel --environment=production --yes >/dev/null 2>&1 \
  || vercel env pull .env.vercel --yes >/dev/null 2>&1 || true

# Variables marked sensitive in Vercel come back as the literal "[SENSITIVE]",
# so a pulled value is only usable if it actually looks like a connection URL.
usable_url() { case "$1" in postgres://*|postgresql://*) return 0 ;; *) return 1 ;; esac; }

DB_URL=""
for candidate in \
  "$(read_env DATABASE_URL_UNPOOLED || true)" \
  "$(read_env DATABASE_URL || true)" \
  "$(sed -n 's/^DATABASE_URL_UNPOOLED=//p' .env.vercel 2>/dev/null | head -1 | tr -d '"')" \
  "$(sed -n 's/^DATABASE_URL=//p' .env.vercel 2>/dev/null | head -1 | tr -d '"')"
do
  if usable_url "$candidate"; then DB_URL="$candidate"; break; fi
done

if [ -z "$DB_URL" ]; then
  cat >&2 <<'MSG'

No DATABASE_URL found.

Attach Postgres first, then re-run this script:
  Vercel -> your project -> Storage -> Create Database -> Neon
  -> Connect Project (all environments)

Or add DATABASE_URL=... to .env.local to use a database you already have.
MSG
  exit 1
fi

step "Applying migrations"
DATABASE_URL="$DB_URL" "$PY" -m alembic upgrade head

step "Seeding content"
DATABASE_URL="$DB_URL" "$PY" -m app.seed

step "Done"
cat <<MSG
Environment variables are set and the database is ready.

Next:
  1. Redeploy so the running deployment picks up the variables:
       vercel redeploy --yes
  2. Sign in to the console at <deployment-url>/admin
     Email:    $(read_env ADMIN_EMAIL)
     Password: see ADMIN_PASSWORD in $ENV_FILE
MSG
