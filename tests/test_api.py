"""End-to-end smoke tests for the Restructuring Screener API."""
from __future__ import annotations


def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


def test_create_and_list_company(client):
    # Create
    resp = client.post("/companies/", json={"name": "Acme Corp", "ticker": "ACME", "sector": "Manufacturing"})
    assert resp.status_code == 201
    company = resp.json()
    assert company["name"] == "Acme Corp"
    assert company["id"] is not None

    # List
    resp = client.get("/companies/")
    assert resp.status_code == 200
    companies = resp.json()
    assert len(companies) >= 1


def test_get_company_not_found(client):
    resp = client.get("/companies/99999")
    assert resp.status_code == 404


def test_create_event_triggers_score(client):
    # Create company first
    resp = client.post("/companies/", json={"name": "Beta Inc", "ticker": "BETA"})
    assert resp.status_code == 201
    company_id = resp.json()["id"]

    # Ingest event
    resp = client.post("/events/", json={
        "company_id": company_id,
        "event_type": "bankruptcy",
        "description": "Chapter 11 filing",
        "severity": 9.0,
    })
    assert resp.status_code == 201

    # Score should now exist
    resp = client.get(f"/scores/{company_id}")
    assert resp.status_code == 200
    score = resp.json()
    assert 0 <= score["distress_score"] <= 100
    assert 0 <= score["restructuring_significance"] <= 100
    assert 0 <= score["turnaround_opportunity"] <= 100


def test_list_events(client):
    resp = client.get("/events/")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_score_not_found(client):
    resp = client.get("/scores/99999")
    assert resp.status_code == 404


def test_company_detail_with_score(client):
    # Create company
    resp = client.post("/companies/", json={"name": "Gamma LLC", "ticker": "GAMA"})
    assert resp.status_code == 201
    company_id = resp.json()["id"]

    # Ingest two events
    for event_type, severity in [("going_concern_warning", 8.0), ("debt_restructuring", 7.5)]:
        client.post("/events/", json={"company_id": company_id, "event_type": event_type, "severity": severity})

    # Verify company detail contains latest score
    resp = client.get(f"/companies/{company_id}")
    assert resp.status_code == 200
    detail = resp.json()
    assert detail["latest_score"] is not None
    assert "explanation" in detail["latest_score"]
