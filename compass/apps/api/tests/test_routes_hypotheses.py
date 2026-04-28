"""Integration tests for /api/v1/hypotheses routes."""
import pytest
from tests.conftest import HYPOTHESIS_PAYLOAD


@pytest.mark.anyio
async def test_create_hypothesis(client):
    r = await client.post("/api/v1/hypotheses/", json=HYPOTHESIS_PAYLOAD)
    assert r.status_code == 201
    data = r.json()
    assert data["title"] == HYPOTHESIS_PAYLOAD["title"]
    assert data["status"] == "draft"
    assert "id" in data


@pytest.mark.anyio
async def test_list_hypotheses_empty(client):
    r = await client.get("/api/v1/hypotheses/")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.anyio
async def test_list_hypotheses_returns_created(client):
    await client.post("/api/v1/hypotheses/", json=HYPOTHESIS_PAYLOAD)
    r = await client.get("/api/v1/hypotheses/")
    assert r.status_code == 200
    titles = [h["title"] for h in r.json()]
    assert HYPOTHESIS_PAYLOAD["title"] in titles


@pytest.mark.anyio
async def test_get_hypothesis_by_id(client):
    created = (await client.post("/api/v1/hypotheses/", json=HYPOTHESIS_PAYLOAD)).json()
    r = await client.get(f"/api/v1/hypotheses/{created['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == created["id"]


@pytest.mark.anyio
async def test_get_hypothesis_not_found(client):
    from uuid import uuid4
    r = await client.get(f"/api/v1/hypotheses/{uuid4()}")
    assert r.status_code == 404


@pytest.mark.anyio
async def test_patch_hypothesis_status(client):
    created = (await client.post("/api/v1/hypotheses/", json=HYPOTHESIS_PAYLOAD)).json()
    r = await client.patch(f"/api/v1/hypotheses/{created['id']}", json={"status": "parked"})
    assert r.status_code == 200
    assert r.json()["status"] == "parked"


@pytest.mark.anyio
async def test_patch_hypothesis_score(client):
    created = (await client.post("/api/v1/hypotheses/", json=HYPOTHESIS_PAYLOAD)).json()
    r = await client.patch(
        f"/api/v1/hypotheses/{created['id']}",
        json={"overall_score": 8.2, "confidence_score": 0.75},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["overall_score"] == pytest.approx(8.2)
    assert data["confidence_score"] == pytest.approx(0.75)


@pytest.mark.anyio
async def test_list_filter_domain(client):
    await client.post("/api/v1/hypotheses/", json={**HYPOTHESIS_PAYLOAD, "domain": "lkm"})
    await client.post("/api/v1/hypotheses/", json={**HYPOTHESIS_PAYLOAD, "domain": "lubricants"})
    r = await client.get("/api/v1/hypotheses/?domain=lkm")
    assert r.status_code == 200
    assert all(h["domain"] == "lkm" for h in r.json())


@pytest.mark.anyio
async def test_evaluations_empty(client):
    created = (await client.post("/api/v1/hypotheses/", json=HYPOTHESIS_PAYLOAD)).json()
    r = await client.get(f"/api/v1/hypotheses/{created['id']}/evaluations")
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.anyio
async def test_advance_stage(client):
    created = (await client.post("/api/v1/hypotheses/", json=HYPOTHESIS_PAYLOAD)).json()
    r = await client.post(f"/api/v1/hypotheses/{created['id']}/advance")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "queued"
    assert data["hypothesis_id"] == created["id"]
