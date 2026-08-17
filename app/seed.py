"""Idempotent database seed.

    python -m app.seed              # create tables if needed, insert missing content
    python -m app.seed --reset      # drop and recreate everything (development only)

Existing rows are never overwritten, so running it again after content edits is
safe: it only inserts what is missing and reports what it skipped.
"""

from __future__ import annotations

import argparse
import asyncio
import secrets
import sys

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.base import Base
from app.db.models import (
    AdSlot,
    BucketItem,
    BucketType,
    Experience,
    Metric,
    Project,
    Section,
    SiteSetting,
    Skill,
    SkillGroup,
)
from app.db.session import SessionFactory, engine
from app.seed_data import (
    AD_SLOTS,
    BUCKET_ITEMS,
    EXPERIENCES,
    METRICS,
    PROJECTS,
    SECTIONS,
    SITE_SETTINGS,
    SKILL_GROUPS,
)
from app.services.auth import ensure_admin_user


async def _count(session: AsyncSession, model) -> int:
    result = await session.execute(select(func.count()).select_from(model))
    return int(result.scalar_one())


async def create_schema(reset: bool = False) -> None:
    async with engine.begin() as conn:
        if reset:
            await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async def seed_settings(session: AsyncSession) -> str:
    if await _count(session, SiteSetting):
        return "site settings already present"
    session.add(SiteSetting(**SITE_SETTINGS))
    await session.commit()
    return "site settings created"


async def seed_sections(session: AsyncSession) -> str:
    result = await session.execute(select(Section.key))
    existing = set(result.scalars().all())
    created = 0
    for payload in SECTIONS:
        if payload["key"] in existing:
            continue
        data = dict(payload)
        data.setdefault("show_in_nav", True)
        session.add(Section(**data))
        created += 1
    await session.commit()
    return f"sections: {created} created, {len(existing)} kept"


async def seed_metrics(session: AsyncSession) -> str:
    if await _count(session, Metric):
        return "metrics already present"
    for payload in METRICS:
        session.add(Metric(**payload))
    await session.commit()
    return f"metrics: {len(METRICS)} created"


async def seed_skills(session: AsyncSession) -> str:
    if await _count(session, SkillGroup):
        return "skill groups already present"
    for payload in SKILL_GROUPS:
        group_payload = dict(payload)  # copy: never mutate the imported seed data
        skills = group_payload.pop("skills")
        group = SkillGroup(**group_payload)
        session.add(group)
        await session.flush()
        for index, (name, details) in enumerate(skills, start=1):
            session.add(
                Skill(group_id=group.id, name=name, details=list(details), position=index * 10)
            )
    await session.commit()
    return f"skill groups: {len(SKILL_GROUPS)} created"


async def seed_projects(session: AsyncSession) -> str:
    if await _count(session, Project):
        return "projects already present"
    for payload in PROJECTS:
        session.add(Project(**payload))
    await session.commit()
    return f"projects: {len(PROJECTS)} created"


async def seed_experience(session: AsyncSession) -> str:
    if await _count(session, Experience):
        return "experience already present"
    for payload in EXPERIENCES:
        session.add(Experience(**payload))
    await session.commit()
    return f"experience: {len(EXPERIENCES)} created"


async def seed_bucket(session: AsyncSession) -> str:
    if await _count(session, BucketItem):
        return "bucket items already present"
    for item_type, title, target, note, progress, position in BUCKET_ITEMS:
        session.add(
            BucketItem(
                title=title,
                item_type=BucketType(item_type),
                target=target,
                note=note,
                progress=progress,
                position=position,
            )
        )
    await session.commit()
    return f"bucket items: {len(BUCKET_ITEMS)} created"


async def seed_ad_slots(session: AsyncSession) -> str:
    result = await session.execute(select(AdSlot.key))
    existing = set(result.scalars().all())
    created = 0
    for payload in AD_SLOTS:
        if payload["key"] in existing:
            continue
        session.add(AdSlot(**payload))
        created += 1
    await session.commit()
    return f"ad slots: {created} created, {len(existing)} kept"


async def run(reset: bool = False) -> None:
    await create_schema(reset=reset)

    async with SessionFactory() as session:
        steps = [
            await seed_settings(session),
            await seed_sections(session),
            await seed_metrics(session),
            await seed_skills(session),
            await seed_projects(session),
            await seed_experience(session),
            await seed_bucket(session),
            await seed_ad_slots(session),
        ]

        password = settings.admin_password
        generated = False
        if not password:
            password = secrets.token_urlsafe(12)
            generated = True

        user, created = await ensure_admin_user(session, settings.admin_email, password)
        if created:
            steps.append(f"admin user created: {user.email}")
            if generated:
                steps.append(f"GENERATED PASSWORD (save it now): {password}")
        else:
            steps.append(f"admin user already exists: {user.email}")

    for line in steps:
        print(f"  - {line}")
    print("\nSeed complete.")
    await engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed the portfolio database")
    parser.add_argument(
        "--reset", action="store_true", help="drop all tables first (development only)"
    )
    args = parser.parse_args()

    if args.reset and settings.environment == "production":
        print("Refusing to reset a production database.", file=sys.stderr)
        return 2

    print(f"Seeding {settings.environment} database...")
    asyncio.run(run(reset=args.reset))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
