"""Database models.

Content is split into typed tables so the admin can offer real forms per
content type rather than a single free-text blob. Every mutation is written to
content_revisions (previous + next payload) which gives both an audit trail
and one-click rollback.
"""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

# JSONB on Postgres, plain JSON on SQLite (used by the test suite).
JSONType = JSON().with_variant(JSONB(), "postgresql")


class UserRole(str, enum.Enum):
    admin = "admin"
    editor = "editor"
    viewer = "viewer"


class EnquiryStatus(str, enum.Enum):
    new = "new"
    in_discussion = "in_discussion"
    won = "won"
    declined = "declined"
    spam = "spam"


class AdSlotStatus(str, enum.Enum):
    vacant = "vacant"
    booked = "booked"
    reserved = "reserved"


class BucketType(str, enum.Enum):
    skill = "skill"
    goal = "goal"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"), default=UserRole.admin, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    totp_secret: Mapped[str | None] = mapped_column(String(64), nullable=True)
    failed_login_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"<User {self.email} {self.role.value}>"


class SiteSetting(Base, TimestampMixin):
    """Single row holding global site identity and contact details."""

    __tablename__ = "site_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_name: Mapped[str] = mapped_column(String(120), nullable=False)
    role_title: Mapped[str] = mapped_column(String(160), default="", nullable=False)
    meta_title: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    meta_description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    email: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    phone: Mapped[str] = mapped_column(String(40), default="", nullable=False)
    location: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    linkedin_url: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    github_url: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    resume_url: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    profile_image: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    availability_note: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    default_theme: Mapped[str] = mapped_column(String(10), default="dark", nullable=False)
    analytics_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Section(Base, TimestampMixin):
    """A page section. `body` holds copy that varies by section type."""

    __tablename__ = "sections"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    nav_label: Mapped[str] = mapped_column(String(60), default="", nullable=False)
    heading: Mapped[str] = mapped_column(String(160), default="", nullable=False)
    subheading: Mapped[str] = mapped_column(Text, default="", nullable=False)
    body: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    show_in_nav: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Metric(Base, TimestampMixin):
    __tablename__ = "metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    value: Mapped[str] = mapped_column(String(20), nullable=False)
    numeric_target: Mapped[float | None] = mapped_column(nullable=True)
    prefix: Mapped[str] = mapped_column(String(5), default="", nullable=False)
    suffix: Mapped[str] = mapped_column(String(5), default="", nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class SkillGroup(Base, TimestampMixin):
    __tablename__ = "skill_groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    accent: Mapped[str] = mapped_column(String(20), default="cyan", nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    skills: Mapped[list["Skill"]] = relationship(
        back_populates="group",
        cascade="all, delete-orphan",
        order_by="Skill.position",
        lazy="selectin",
    )


class Skill(Base, TimestampMixin):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("skill_groups.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    details: Mapped[list] = mapped_column(JSONType, default=list, nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    group: Mapped[SkillGroup] = relationship(back_populates="skills")


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    badge: Mapped[str] = mapped_column(String(60), default="", nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    tech: Mapped[list] = mapped_column(JSONType, default=list, nullable=False)
    link_url: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    link_label: Mapped[str] = mapped_column(String(60), default="", nullable=False)
    tag_label: Mapped[str] = mapped_column(String(80), default="", nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Experience(Base, TimestampMixin):
    __tablename__ = "experiences"

    id: Mapped[int] = mapped_column(primary_key=True)
    role: Mapped[str] = mapped_column(String(200), nullable=False)
    company: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    location: Mapped[str] = mapped_column(String(160), default="", nullable=False)
    period: Mapped[str] = mapped_column(String(80), default="", nullable=False)
    tech: Mapped[list] = mapped_column(JSONType, default=list, nullable=False)
    bullets: Mapped[list] = mapped_column(JSONType, default=list, nullable=False)
    impact: Mapped[str] = mapped_column(Text, default="", nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class BucketItem(Base, TimestampMixin):
    __tablename__ = "bucket_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    item_type: Mapped[BucketType] = mapped_column(
        Enum(BucketType, name="bucket_type"), default=BucketType.skill, nullable=False
    )
    target: Mapped[str] = mapped_column(String(60), default="TBD", nullable=False)
    note: Mapped[str] = mapped_column(Text, default="", nullable=False)
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class AdSlot(Base, TimestampMixin):
    __tablename__ = "ad_slots"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(60), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    size: Mapped[str] = mapped_column(String(80), default="", nullable=False)
    placement: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    reach: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    tier: Mapped[str] = mapped_column(String(30), default="", nullable=False)
    status: Mapped[AdSlotStatus] = mapped_column(
        Enum(AdSlotStatus, name="ad_slot_status"), default=AdSlotStatus.vacant, nullable=False
    )
    brand: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    tagline: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    link_url: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    logo_url: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    monthly_rate: Mapped[str] = mapped_column(String(60), default="", nullable=False)
    booked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Enquiry(Base, TimestampMixin):
    """Ad board submissions, stored before the notification mail is sent."""

    __tablename__ = "enquiries"

    id: Mapped[int] = mapped_column(primary_key=True)
    slot_key: Mapped[str] = mapped_column(String(60), default="", nullable=False)
    slot_name: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    brand: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    budget_amount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="INR", nullable=False)
    billing_cycle: Mapped[str] = mapped_column(String(40), default="Per month", nullable=False)
    message: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[EnquiryStatus] = mapped_column(
        Enum(EnquiryStatus, name="enquiry_status"), default=EnquiryStatus.new, nullable=False
    )
    mail_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mail_error: Mapped[str] = mapped_column(Text, default="", nullable=False)
    source_ip: Mapped[str] = mapped_column(String(60), default="", nullable=False)
    user_agent: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    admin_notes: Mapped[str] = mapped_column(Text, default="", nullable=False)


class MediaAsset(Base, TimestampMixin):
    """An image held in Vercel Blob, uploaded through the admin console."""

    __tablename__ = "media_assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(200), nullable=False)
    pathname: Mapped[str] = mapped_column(String(300), unique=True, nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str] = mapped_column(String(60), default="", nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    alt_text: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    used_for: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    uploaded_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    @property
    def size_kb(self) -> int:
        return max(1, round(self.size_bytes / 1024))


class ContentRevision(Base, TimestampMixin):
    """Before/after snapshot of every content mutation, for audit and rollback."""

    __tablename__ = "content_revisions"
    __table_args__ = (UniqueConstraint("entity", "entity_id", "version", name="uq_revision"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    entity: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    action: Mapped[str] = mapped_column(String(20), default="update", nullable=False)
    previous: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    current: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    changed_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class AuditLog(Base, TimestampMixin):
    """Security-relevant events: logins, lockouts, publishes, deletions."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    event: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    detail: Mapped[str] = mapped_column(Text, default="", nullable=False)
    actor_email: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    ip_address: Mapped[str] = mapped_column(String(60), default="", nullable=False)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class AgentJob(Base, TimestampMixin):
    """Queued work for future AI/agent features.

    Serverless requests cannot run long tasks, so agent work is enqueued here
    and drained by a scheduled worker (Vercel Cron -> /api/v1/jobs/drain).
    """

    __tablename__ = "agent_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_type: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="queued", index=True, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    result: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    error: Mapped[str] = mapped_column(Text, default="", nullable=False)
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
