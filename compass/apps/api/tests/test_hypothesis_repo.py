"""Tests for HypothesisRepository."""
import pytest
from fastapi import HTTPException

from app.repositories.hypothesis import HypothesisRepository
from app.schemas.hypothesis import HypothesisCreate, HypothesisUpdate
from tests.conftest import HYPOTHESIS_PAYLOAD


def _make_create(**kwargs) -> HypothesisCreate:
    return HypothesisCreate(**{**HYPOTHESIS_PAYLOAD, **kwargs})


@pytest.mark.anyio
async def test_create_returns_read_schema(db_session):
    repo = HypothesisRepository(db_session)
    result = await repo.create(_make_create())
    assert result.id is not None
    assert result.title == HYPOTHESIS_PAYLOAD["title"]
    assert result.status == "draft"
    assert result.confidence_score == 0.0


@pytest.mark.anyio
async def test_get_or_404_found(db_session):
    repo = HypothesisRepository(db_session)
    created = await repo.create(_make_create())
    fetched = await repo.get_or_404(created.id)
    assert fetched.id == created.id


@pytest.mark.anyio
async def test_get_or_404_missing(db_session):
    from uuid import uuid4
    repo = HypothesisRepository(db_session)
    with pytest.raises(HTTPException) as exc:
        await repo.get_or_404(uuid4())
    assert exc.value.status_code == 404


@pytest.mark.anyio
async def test_list_empty(db_session):
    repo = HypothesisRepository(db_session)
    result = await repo.list()
    assert isinstance(result, list)


@pytest.mark.anyio
async def test_list_filter_by_domain(db_session):
    repo = HypothesisRepository(db_session)
    await repo.create(_make_create(domain="lkm"))
    await repo.create(_make_create(domain="lubricants"))
    lkm = await repo.list(domain="lkm")
    lub = await repo.list(domain="lubricants")
    assert all(h.domain == "lkm" for h in lkm)
    assert all(h.domain == "lubricants" for h in lub)


@pytest.mark.anyio
async def test_list_filter_by_status(db_session):
    repo = HypothesisRepository(db_session)
    h = await repo.create(_make_create())
    await repo.update(h.id, HypothesisUpdate(status="accepted"))
    accepted = await repo.list(status="accepted")
    drafts = await repo.list(status="draft")
    assert any(x.id == h.id for x in accepted)
    assert all(x.id != h.id for x in drafts)


@pytest.mark.anyio
async def test_update_fields(db_session):
    repo = HypothesisRepository(db_session)
    h = await repo.create(_make_create())
    updated = await repo.update(h.id, HypothesisUpdate(
        status="tech_evaluated",
        overall_score=7.5,
        confidence_score=0.8,
    ))
    assert updated.status == "tech_evaluated"
    assert updated.overall_score == 7.5
    assert updated.confidence_score == 0.8


@pytest.mark.anyio
async def test_update_partial(db_session):
    """Partial update must not overwrite unset fields."""
    repo = HypothesisRepository(db_session)
    h = await repo.create(_make_create())
    await repo.update(h.id, HypothesisUpdate(overall_score=5.0))
    updated = await repo.update(h.id, HypothesisUpdate(status="parked"))
    assert updated.overall_score == 5.0
    assert updated.status == "parked"


@pytest.mark.anyio
async def test_list_limit_offset(db_session):
    repo = HypothesisRepository(db_session)
    for i in range(5):
        await repo.create(_make_create(title=f"Гипотеза {i}"))
    page1 = await repo.list(limit=3, offset=0)
    page2 = await repo.list(limit=3, offset=3)
    assert len(page1) == 3
    assert len(page2) >= 2
    ids1 = {h.id for h in page1}
    ids2 = {h.id for h in page2}
    assert ids1.isdisjoint(ids2)
