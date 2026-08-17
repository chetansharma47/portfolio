"""Content services: reads for the public site, writes with revision history."""

from __future__ import annotations

from typing import Any, Sequence, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.inspection import inspect as sa_inspect

from app.db.base import Base
from app.db.models import (
    AdSlot,
    AdSlotStatus,
    BucketItem,
    ContentRevision,
    Experience,
    Metric,
    Project,
    Section,
    SiteSetting,
    SkillGroup,
)

ModelT = TypeVar("ModelT", bound=Base)

# Entity registry drives the generic admin list/edit screens.
CONTENT_MODELS: dict[str, type[Base]] = {
    "section": Section,
    "metric": Metric,
    "skill_group": SkillGroup,
    "project": Project,
    "experience": Experience,
    "bucket_item": BucketItem,
    "ad_slot": AdSlot,
    "site_setting": SiteSetting,
}


def serialise(instance: Base) -> dict[str, Any]:
    """Plain dict of column values, safe to store as JSON."""
    payload: dict[str, Any] = {}
    for column in sa_inspect(type(instance)).columns:
        value = getattr(instance, column.key)
        if hasattr(value, "isoformat"):
            value = value.isoformat()
        elif hasattr(value, "value"):  # Enum
            value = value.value
        payload[column.key] = value
    return payload


async def _next_version(session: AsyncSession, entity: str, entity_id: int) -> int:
    result = await session.execute(
        select(func.coalesce(func.max(ContentRevision.version), 0)).where(
            ContentRevision.entity == entity, ContentRevision.entity_id == entity_id
        )
    )
    return int(result.scalar_one()) + 1


async def record_revision(
    session: AsyncSession,
    entity: str,
    entity_id: int,
    *,
    action: str,
    previous: dict[str, Any] | None,
    current: dict[str, Any] | None,
    user_id: int | None,
) -> ContentRevision:
    revision = ContentRevision(
        entity=entity,
        entity_id=entity_id,
        version=await _next_version(session, entity, entity_id),
        action=action,
        previous=previous,
        current=current,
        changed_by_id=user_id,
    )
    session.add(revision)
    return revision


async def apply_update(
    session: AsyncSession,
    instance: Base,
    changes: dict[str, Any],
    *,
    entity: str,
    user_id: int | None,
) -> Base:
    """Update columns, snapshot before/after, commit."""
    previous = serialise(instance)
    columns = {c.key for c in sa_inspect(type(instance)).columns}
    for field, value in changes.items():
        if field in columns and field not in {"id", "created_at", "updated_at"}:
            setattr(instance, field, value)

    await session.flush()
    current = serialise(instance)
    if current != previous:
        await record_revision(
            session,
            entity,
            instance.id,
            action="update",
            previous=previous,
            current=current,
            user_id=user_id,
        )
    await session.commit()
    await session.refresh(instance)
    return instance


async def create_instance(
    session: AsyncSession,
    model: type[ModelT],
    values: dict[str, Any],
    *,
    entity: str,
    user_id: int | None,
) -> ModelT:
    instance = model(**values)
    session.add(instance)
    await session.flush()
    await record_revision(
        session,
        entity,
        instance.id,
        action="create",
        previous=None,
        current=serialise(instance),
        user_id=user_id,
    )
    await session.commit()
    await session.refresh(instance)
    return instance


async def delete_instance(
    session: AsyncSession, instance: Base, *, entity: str, user_id: int | None
) -> None:
    previous = serialise(instance)
    entity_id = instance.id
    await session.delete(instance)
    await session.flush()
    await record_revision(
        session,
        entity,
        entity_id,
        action="delete",
        previous=previous,
        current=None,
        user_id=user_id,
    )
    await session.commit()


async def revisions_for(
    session: AsyncSession, entity: str, entity_id: int, limit: int = 20
) -> Sequence[ContentRevision]:
    result = await session.execute(
        select(ContentRevision)
        .where(ContentRevision.entity == entity, ContentRevision.entity_id == entity_id)
        .order_by(ContentRevision.version.desc())
        .limit(limit)
    )
    return result.scalars().all()


async def rollback_to(
    session: AsyncSession, revision: ContentRevision, *, user_id: int | None
) -> Base | None:
    """Restore the `previous` payload of a revision onto the live row."""
    model = CONTENT_MODELS.get(revision.entity)
    if model is None or revision.previous is None:
        return None
    instance = await session.get(model, revision.entity_id)
    if instance is None:
        return None
    payload = {k: v for k, v in revision.previous.items() if k not in {"id", "created_at", "updated_at"}}
    return await apply_update(
        session, instance, payload, entity=revision.entity, user_id=user_id
    )


# --- Public reads ----------------------------------------------------------

async def get_settings_row(session: AsyncSession) -> SiteSetting | None:
    result = await session.execute(select(SiteSetting).order_by(SiteSetting.id).limit(1))
    return result.scalar_one_or_none()


async def _ordered(session: AsyncSession, model: type[ModelT], *filters) -> list[ModelT]:
    stmt = select(model)
    for condition in filters:
        stmt = stmt.where(condition)
    stmt = stmt.order_by(model.position, model.id)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def public_page_context(session: AsyncSession) -> dict[str, Any]:
    """Everything the public template needs, in one round of queries."""
    sections = await _ordered(session, Section, Section.is_visible.is_(True))
    return {
        "settings_row": await get_settings_row(session),
        "sections": {s.key: s for s in sections},
        "nav_sections": [s for s in sections if s.show_in_nav],
        "metrics": await _ordered(session, Metric, Metric.is_visible.is_(True)),
        "skill_groups": await _ordered(session, SkillGroup, SkillGroup.is_visible.is_(True)),
        "projects": await _ordered(session, Project, Project.is_published.is_(True)),
        "experiences": await _ordered(session, Experience, Experience.is_published.is_(True)),
        "bucket_items": await _ordered(session, BucketItem, BucketItem.is_visible.is_(True)),
        "ad_slots": await _ordered(session, AdSlot, AdSlot.is_visible.is_(True)),
    }


def bucket_stats(items: Sequence[BucketItem]) -> dict[str, int]:
    total = len(items)
    done = sum(1 for i in items if i.progress >= 100)
    active = sum(1 for i in items if 0 < i.progress < 100)
    average = round(sum(i.progress for i in items) / total) if total else 0
    return {"total": total, "done": done, "active": active, "average": average}


def slot_is_vacant(slot: AdSlot) -> bool:
    return slot.status != AdSlotStatus.booked
