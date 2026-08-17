"""Admin authentication, guards and content control."""

from __future__ import annotations

import os
import sqlite3

from tests.conftest import TEST_DB


def test_admin_requires_login(client):
    response = client.get("/admin", follow_redirects=False)
    assert response.status_code == 303
    assert "/admin/login" in response.headers["location"]


def test_login_rejects_bad_password(client):
    page = client.get("/admin/login")
    csrf = page.cookies.get("portfolio_csrf")
    response = client.post(
        "/admin/login",
        data={"email": os.environ["ADMIN_EMAIL"], "password": "wrong", "csrf_token": csrf},
    )
    assert response.status_code == 401
    assert "incorrect" in response.text.lower()


def test_login_rejects_missing_csrf(client):
    response = client.post(
        "/admin/login",
        data={"email": os.environ["ADMIN_EMAIL"], "password": os.environ["ADMIN_PASSWORD"]},
    )
    assert response.status_code == 403


def test_failed_login_is_audited(client):
    page = client.get("/admin/login")
    csrf = page.cookies.get("portfolio_csrf")
    client.post(
        "/admin/login",
        data={"email": os.environ["ADMIN_EMAIL"], "password": "nope", "csrf_token": csrf},
    )
    events = [
        row[0]
        for row in sqlite3.connect(TEST_DB).execute("select event from audit_logs")
    ]
    assert "login.failed" in events


def test_dashboard_after_login(admin_client):
    response = admin_client.get("/admin")
    assert response.status_code == 200
    assert "Dashboard" in response.text
    assert response.headers["cache-control"] == "no-store, private"
    assert response.headers["x-robots-tag"] == "noindex, nofollow"


def test_section_edit_updates_public_page(admin_client):
    response = admin_client.get("/admin/content/sections")
    assert response.status_code == 200

    # Find the hero section id from the database.
    hero_id = sqlite3.connect(TEST_DB).execute(
        "select id from sections where key = 'hero'"
    ).fetchone()[0]

    form = admin_client.get(f"/admin/content/sections/{hero_id}")
    assert form.status_code == 200

    new_heading = "Backend and AI Engineer"  # no ampersand: kept simple so HTML escaping is not the subject of this test
    response = admin_client.post(
        f"/admin/content/sections/{hero_id}",
        data={
            "csrf_token": admin_client.csrf_token,
            "key": "hero",
            "nav_label": "",
            "heading": new_heading,
            "subheading": "Updated in a test.",
            "body": "{}",
            "position": "10",
            "is_visible": "1",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    assert new_heading in admin_client.get("/").text

    # show_in_nav was omitted, so the checkbox must now be false.
    show_in_nav = sqlite3.connect(TEST_DB).execute(
        "select show_in_nav from sections where key = 'hero'"
    ).fetchone()[0]
    assert show_in_nav == 0


def test_edit_records_revision_and_rolls_back(admin_client):
    conn = sqlite3.connect(TEST_DB)
    project_id, original_title = conn.execute(
        "select id, title from projects order by position limit 1"
    ).fetchone()

    admin_client.post(
        f"/admin/content/projects/{project_id}",
        data={
            "csrf_token": admin_client.csrf_token,
            "title": "Temporarily renamed project",
            "badge": "Test",
            "description": "changed",
            "tech": "Java\nSpring",
            "link_url": "",
            "link_label": "",
            "tag_label": "",
            "position": "10",
            "is_published": "1",
        },
        follow_redirects=False,
    )

    conn = sqlite3.connect(TEST_DB)
    assert conn.execute(
        "select title from projects where id = ?", (project_id,)
    ).fetchone()[0] == "Temporarily renamed project"

    version = conn.execute(
        "select version from content_revisions where entity='project' and entity_id=?"
        " order by version desc limit 1",
        (project_id,),
    ).fetchone()[0]

    response = admin_client.post(
        f"/admin/content/projects/{project_id}/rollback/{version}",
        data={"csrf_token": admin_client.csrf_token},
        follow_redirects=False,
    )
    assert response.status_code == 303

    restored = sqlite3.connect(TEST_DB).execute(
        "select title from projects where id = ?", (project_id,)
    ).fetchone()[0]
    assert restored == original_title


def test_create_and_delete_bucket_item(admin_client):
    response = admin_client.post(
        "/admin/content/bucket/new",
        data={
            "csrf_token": admin_client.csrf_token,
            "title": "Learn Rust basics",
            "item_type": "skill",
            "target": "Q2 2027",
            "note": "Systems level fluency.",
            "progress": "5",
            "position": "200",
            "is_visible": "1",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    conn = sqlite3.connect(TEST_DB)
    new_id = conn.execute(
        "select id from bucket_items where title = 'Learn Rust basics'"
    ).fetchone()[0]
    assert "Learn Rust basics" in admin_client.get("/").text

    response = admin_client.post(
        f"/admin/content/bucket/{new_id}/delete",
        data={"csrf_token": admin_client.csrf_token},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "Learn Rust basics" not in admin_client.get("/").text

    actions = [
        row[0]
        for row in sqlite3.connect(TEST_DB).execute(
            "select action from content_revisions where entity='bucket_item' and entity_id=?",
            (new_id,),
        )
    ]
    assert "create" in actions and "delete" in actions


def test_invalid_json_field_is_reported(admin_client):
    hero_id = sqlite3.connect(TEST_DB).execute(
        "select id from sections where key = 'hero'"
    ).fetchone()[0]

    response = admin_client.post(
        f"/admin/content/sections/{hero_id}",
        data={
            "csrf_token": admin_client.csrf_token,
            "key": "hero",
            "heading": "Still fine",
            "subheading": "",
            "body": "{not valid json",
            "position": "10",
        },
    )
    assert response.status_code == 400
    assert "JSON field is invalid" in response.text


def test_enquiry_status_update(admin_client):
    admin_client.post(
        "/api/v1/enquiries",
        json={
            "brand": "Status Test",
            "email": "s@t.com",
            "budget": 500,
            "message": "checking status flow",
        },
    )
    enquiry_id = sqlite3.connect(TEST_DB).execute(
        "select id from enquiries where brand = 'Status Test'"
    ).fetchone()[0]

    response = admin_client.post(
        f"/admin/enquiries/{enquiry_id}",
        data={
            "csrf_token": admin_client.csrf_token,
            "new_status": "in_discussion",
            "admin_notes": "Asked for 2x budget",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    row = sqlite3.connect(TEST_DB).execute(
        "select status, admin_notes from enquiries where id = ?", (enquiry_id,)
    ).fetchone()
    assert row[0] == "in_discussion"
    assert row[1] == "Asked for 2x budget"


def test_unknown_entity_is_404(admin_client):
    assert admin_client.get("/admin/content/not-a-thing").status_code == 404
