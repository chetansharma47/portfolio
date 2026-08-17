"""Declarative admin form definitions.

Each content type lists its editable fields once; the admin list and form
templates are generated from these specs, so adding a field to a model plus an
entry here is all that is needed for it to become editable.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable

from app.db.models import (
    AdSlot,
    AdSlotStatus,
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


@dataclass(slots=True)
class Field_:
    name: str
    label: str
    kind: str = "text"  # text|textarea|number|checkbox|select|lines|json|email|url|image
    help_text: str = ""
    options: list[tuple[str, str]] = field(default_factory=list)
    required: bool = False
    rows: int = 4
    step: str = "1"


@dataclass(slots=True)
class EntitySpec:
    key: str
    model: type
    label: str
    label_plural: str
    icon: str
    columns: list[str]
    fields: list[Field_]
    singleton: bool = False
    order_by: str = "position"
    description: str = ""
    options_provider: Callable[..., Any] | None = None


def _enum_options(enum_cls) -> list[tuple[str, str]]:
    return [(member.value, member.value.replace("_", " ").title()) for member in enum_cls]


SECTION_SPEC = EntitySpec(
    key="sections",
    model=Section,
    label="Section",
    label_plural="Page Sections",
    icon="layout",
    columns=["position", "key", "nav_label", "heading", "is_visible", "show_in_nav"],
    description="Headings, intro copy, ordering and visibility of every block on the public page.",
    fields=[
        Field_("key", "Section key", help_text="Used as the anchor id. Change with care.", required=True),
        Field_("nav_label", "Navigation label"),
        Field_("heading", "Heading"),
        Field_("subheading", "Intro copy", kind="textarea", rows=4),
        Field_("body", "Extra content (JSON)", kind="json", rows=8,
               help_text="Section-specific fields such as hero buttons or board footer lines."),
        Field_("position", "Position", kind="number"),
        Field_("is_visible", "Visible on site", kind="checkbox"),
        Field_("show_in_nav", "Show in navigation", kind="checkbox"),
    ],
)

METRIC_SPEC = EntitySpec(
    key="metrics",
    model=Metric,
    label="Metric",
    label_plural="Impact Metrics",
    icon="chart",
    columns=["position", "value", "label", "is_visible"],
    description="The counter row under the hero.",
    fields=[
        Field_("value", "Display value", required=True, help_text="Shown before the count animation, e.g. 99.9%"),
        Field_("label", "Label", required=True),
        Field_("numeric_target", "Numeric target", kind="number", step="0.1",
               help_text="Used by the count-up animation. Leave empty to skip animating."),
        Field_("prefix", "Prefix"),
        Field_("suffix", "Suffix"),
        Field_("position", "Position", kind="number"),
        Field_("is_visible", "Visible", kind="checkbox"),
    ],
)

SKILL_GROUP_SPEC = EntitySpec(
    key="skill-groups",
    model=SkillGroup,
    label="Skill group",
    label_plural="Skill Groups",
    icon="grid",
    columns=["position", "title", "accent", "is_visible"],
    description="Cards in the technical arsenal section.",
    fields=[
        Field_("title", "Title", required=True),
        Field_("accent", "Accent", kind="select", options=[("cyan", "Cyan"), ("purple", "Purple")]),
        Field_("position", "Position", kind="number"),
        Field_("is_visible", "Visible", kind="checkbox"),
    ],
)

SKILL_SPEC = EntitySpec(
    key="skills",
    model=Skill,
    label="Skill",
    label_plural="Skills",
    icon="tag",
    columns=["position", "name", "group_id"],
    description="Individual pills inside a skill group, with the detail list shown when clicked.",
    fields=[
        Field_("group_id", "Skill group", kind="select", required=True),
        Field_("name", "Name", required=True),
        Field_("details", "Detail lines", kind="lines", rows=6,
               help_text="One bullet per line."),
        Field_("position", "Position", kind="number"),
    ],
)

PROJECT_SPEC = EntitySpec(
    key="projects",
    model=Project,
    label="Project",
    label_plural="Projects",
    icon="briefcase",
    columns=["position", "title", "badge", "is_published"],
    fields=[
        Field_("title", "Title", required=True),
        Field_("badge", "Badge"),
        Field_("description", "Description", kind="textarea", rows=6),
        Field_("tech", "Tech tags", kind="lines", rows=6, help_text="One tag per line."),
        Field_("link_url", "Link URL", kind="url"),
        Field_("link_label", "Link label"),
        Field_("tag_label", "Static tag", help_text="Shown instead of a link, e.g. an employer name."),
        Field_("position", "Position", kind="number"),
        Field_("is_published", "Published", kind="checkbox"),
    ],
)

EXPERIENCE_SPEC = EntitySpec(
    key="experience",
    model=Experience,
    label="Role",
    label_plural="Experience",
    icon="clock",
    columns=["position", "role", "company", "period", "is_published"],
    fields=[
        Field_("role", "Role", required=True),
        Field_("company", "Company"),
        Field_("location", "Location"),
        Field_("period", "Period"),
        Field_("tech", "Tech pills", kind="lines", rows=6),
        Field_("bullets", "Bullet points", kind="lines", rows=10,
               help_text="One achievement per line. Inline HTML such as <strong> is allowed."),
        Field_("impact", "Key impact", kind="textarea", rows=3),
        Field_("position", "Position", kind="number"),
        Field_("is_published", "Published", kind="checkbox"),
    ],
)

BUCKET_SPEC = EntitySpec(
    key="bucket",
    model=BucketItem,
    label="Bucket item",
    label_plural="Bucket & Roadmap",
    icon="target",
    columns=["position", "title", "item_type", "progress", "is_visible"],
    fields=[
        Field_("title", "Title", required=True),
        Field_("item_type", "Type", kind="select", options=_enum_options(BucketType)),
        Field_("target", "Target"),
        Field_("note", "Why it matters", kind="textarea", rows=3),
        Field_("progress", "Progress %", kind="number"),
        Field_("position", "Position", kind="number"),
        Field_("is_visible", "Visible", kind="checkbox"),
    ],
)

AD_SLOT_SPEC = EntitySpec(
    key="ad-slots",
    model=AdSlot,
    label="Ad slot",
    label_plural="Advertisement Board",
    icon="megaphone",
    columns=["position", "name", "status", "brand", "poster_url", "is_visible"],
    description=(
        "Board panels. Set status to booked, upload the advertiser's poster and add the "
        "click-through link to run a campaign."
    ),
    fields=[
        Field_("key", "Slot key", required=True),
        Field_("name", "Name", required=True),
        Field_("size", "Size"),
        Field_("placement", "Placement"),
        Field_("reach", "Audience"),
        Field_("tier", "Tier", kind="select", options=[("", "Standard"), ("premium", "Premium")]),
        Field_("monthly_rate", "Indicative rate"),
        Field_("status", "Status", kind="select", options=_enum_options(AdSlotStatus)),
        Field_("brand", "Brand name"),
        Field_("poster_url", "Advertisement poster", kind="image",
               help_text="Upload the creative the brand supplied. It fills the whole panel; "
                         "the logo and tagline below are only used when no poster is set."),
        Field_("poster_alt", "Poster alt text",
               help_text="Describes the poster for screen readers and when the image fails to load."),
        Field_("tagline", "Brand tagline"),
        Field_("link_url", "Click-through link", kind="url"),
        Field_("logo_url", "Brand logo", kind="image",
               help_text="Upload the brand logo. Used with the tagline only when no poster "
                         "has been uploaded."),
        Field_("position", "Position", kind="number"),
        Field_("is_visible", "Visible", kind="checkbox"),
    ],
)

SETTINGS_SPEC = EntitySpec(
    key="settings",
    model=SiteSetting,
    label="Site settings",
    label_plural="Site Settings",
    icon="settings",
    columns=[],
    singleton=True,
    order_by="id",
    description="Identity, contact details and metadata used across the site.",
    fields=[
        Field_("owner_name", "Owner name", required=True),
        Field_("role_title", "Role title"),
        Field_("meta_title", "Meta title"),
        Field_("meta_description", "Meta description", kind="textarea", rows=3),
        Field_("email", "Email", kind="email"),
        Field_("phone", "Phone"),
        Field_("location", "Location"),
        Field_("linkedin_url", "LinkedIn URL", kind="url"),
        Field_("github_url", "GitHub URL", kind="url"),
        Field_("resume_url", "Resume URL", kind="url"),
        Field_("profile_image", "Profile image", kind="image",
               help_text="Upload a new photo to replace the current one. Stored in Vercel Blob."),
        Field_("availability_note", "Availability badge"),
        Field_("default_theme", "Default theme", kind="select",
               options=[("dark", "Dark"), ("light", "Light")]),
        Field_("analytics_enabled", "Analytics enabled", kind="checkbox"),
    ],
)

ENTITY_SPECS: dict[str, EntitySpec] = {
    spec.key: spec
    for spec in (
        SECTION_SPEC,
        METRIC_SPEC,
        SKILL_GROUP_SPEC,
        SKILL_SPEC,
        PROJECT_SPEC,
        EXPERIENCE_SPEC,
        BUCKET_SPEC,
        AD_SLOT_SPEC,
        SETTINGS_SPEC,
    )
}

# Maps an admin route key to the entity name used in the revision log.
REVISION_ENTITY = {
    "sections": "section",
    "metrics": "metric",
    "skill-groups": "skill_group",
    "skills": "skill",
    "projects": "project",
    "experience": "experience",
    "bucket": "bucket_item",
    "ad-slots": "ad_slot",
    "settings": "site_setting",
}


def parse_form_value(field_: Field_, raw: str | None) -> Any:
    """Convert a submitted string into the value the column expects."""
    if field_.kind == "checkbox":
        return raw is not None and raw not in {"", "0", "false", "off"}

    value = (raw or "").strip()

    if field_.kind == "number":
        if value == "":
            return None if field_.step != "1" else 0
        return float(value) if field_.step != "1" else int(float(value))

    if field_.kind == "lines":
        return [line.strip() for line in value.splitlines() if line.strip()]

    if field_.kind == "json":
        if not value:
            return {}
        return json.loads(value)

    if field_.kind == "select" and field_.name == "group_id":
        return int(value) if value else None

    # "image" arrives as a hidden field holding the current value. The router
    # replaces it with an uploaded file's URL, or clears it on request.
    if field_.kind == "image":
        return value

    return value


def format_field_value(field_: Field_, value: Any) -> str:
    """Render a stored value back into a form control."""
    if value is None:
        return ""
    if field_.kind == "lines":
        return "\n".join(str(item) for item in (value or []))
    if field_.kind == "json":
        return json.dumps(value, indent=2, ensure_ascii=False) if value else ""
    if hasattr(value, "value"):  # Enum
        return str(value.value)
    if isinstance(value, bool):
        return "1" if value else ""
    return str(value)
