"""API smoke tests against the seeded sample dataset."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from applytrack.api.app import create_app
from applytrack.db import SessionLocal
from applytrack.sample_data.loader import load_sample_data


@pytest.fixture
def client():
    return TestClient(create_app())


@pytest.fixture
def seeded():
    s = SessionLocal()
    try:
        load_sample_data(s)
        s.commit()
    finally:
        s.close()


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_account_status_disconnected(client):
    resp = client.get("/api/account")
    assert resp.status_code == 200
    assert resp.json()["connected"] is False


def test_applications_list(client, seeded):
    resp = client.get("/api/applications")
    assert resp.status_code == 200
    apps = resp.json()
    companies = {a["company"] for a in apps}
    # Sample set includes Helvetia-tech, Northwind, Lakeside, etc.
    assert any("lakeside" in c.lower() for c in companies)


def test_stats(client, seeded):
    resp = client.get("/api/applications/stats")
    assert resp.status_code == 200
    stats = resp.json()
    assert stats["offers"] >= 1
    assert stats["rejections"] >= 1
    assert stats["total_applied"] >= 4


def test_offer_status_derived(client, seeded):
    apps = client.get("/api/applications").json()
    lakeside = next(a for a in apps if "lakeside" in a["company"].lower())
    assert lakeside["current_status"] == "offer"


def test_detail_has_timeline(client, seeded):
    apps = client.get("/api/applications").json()
    app_id = apps[0]["id"]
    detail = client.get(f"/api/applications/{app_id}").json()
    assert "emails" in detail
    assert len(detail["emails"]) >= 1


def test_noise_is_filtered_but_kept(client, seeded):
    # Newsletters are excluded from applications…
    apps = client.get("/api/applications").json()
    assert not any("linkedin" in (a["company"] or "").lower() for a in apps)
    # …but retained and listable.
    noise = client.get("/api/emails/noise").json()
    assert len(noise) >= 1


def test_override_changes_status(client, seeded):
    apps = client.get("/api/applications").json()
    northwind = next(a for a in apps if "northwind" in a["company"].lower())
    detail = client.get(f"/api/applications/{northwind['id']}").json()
    rejection_email = next(e for e in detail["emails"] if e["effective_intent"] == "rejection")

    # Override the rejection to an interview invite → status should change.
    resp = client.patch(
        f"/api/emails/{rejection_email['id']}/override", json={"intent": "interview_invite"}
    )
    assert resp.status_code == 200
    updated = client.get(f"/api/applications/{northwind['id']}").json()
    assert updated["current_status"] == "interview_invite"
