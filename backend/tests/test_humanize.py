"""End-to-end tests for the humanization service and API.

These run the real Qwen2.5-0.5B + LoRA pipeline on CPU, so they are slower than
the unit tests. The model is loaded once per session.
"""

import pytest

from app.services.humanize_service import HumanizeService, UnsupportedToolError


SAMPLE = (
    "It is important to note that the implementation of the utilization of modern "
    "methodology facilitates the optimization of comprehensive subsequent results. "
    "Furthermore, this approach leverages significant improvements in overall performance."
)


@pytest.fixture(scope="session")
def service():
    return HumanizeService()


@pytest.mark.asyncio
async def test_humanize_returns_non_empty_text(service):
    result = await service.humanize(SAMPLE, tone="academic", tool="humanize")
    assert result.text.strip()
    assert len(result.text.split()) > 5
    assert result.preservation is not None
    assert 0.0 <= result.preservation["composite_score"] <= 1.0


@pytest.mark.asyncio
async def test_humanize_reports_scores(service):
    result = await service.humanize(SAMPLE, tone="general", tool="humanize")
    scores = result.preservation["scores"]
    for key in ("semantic", "ner", "keyword", "factual", "intent"):
        assert 0.0 <= scores[key] <= 1.0


@pytest.mark.asyncio
async def test_converged_result_preserves_locked_keywords(service):
    result = await service.humanize(
        SAMPLE,
        tone="academic",
        locked_keywords=["methodology"],
        tool="humanize",
    )
    if result.converged:
        assert result.preservation["missing_keywords"] == []


@pytest.mark.asyncio
async def test_grammar_tool_is_deterministic(service):
    text = "  this is   a test with bad   spacing ."
    result = await service.humanize(text, tool="grammar")
    assert result.text == "This is a test with bad spacing."


@pytest.mark.asyncio
async def test_translate_tool_is_rejected(service):
    with pytest.raises(UnsupportedToolError):
        await service.humanize(SAMPLE, tool="translate")


@pytest.mark.asyncio
async def test_evaluate_only_scores_a_candidate(service):
    report = await service.evaluate_only(
        "Acme Corp raised 40 million dollars in 2026.",
        "Acme Corp raised 40 million dollars in 2026.",
    )
    assert report["composite_score"] > 0.9
    assert report["scores"]["semantic"] > 0.9


@pytest.mark.asyncio
async def test_api_humanize_endpoint(async_client):
    payload = {
        "text": "This is a test article about artificial intelligence and automation.",
        "tone": "academic",
        "locked_keywords": ["artificial intelligence"],
        "tool": "humanize",
    }
    response = await async_client.post("/api/humanize", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["result"].strip()
    assert "processing_time" in data
    meta = data["metadata"]
    assert meta["tone_applied"] == "academic"
    assert meta["keywords_preserved"] == ["artificial intelligence"]
    assert meta["word_count"] > 0
    assert meta["preservation_score"] is not None
    assert meta["scores"]["semantic"] is not None


@pytest.mark.asyncio
async def test_api_humanize_validation_error(async_client):
    payload = {
        "text": "Short",
        "tone": "general",
        "locked_keywords": [],
        "tool": "humanize",
    }
    response = await async_client.post("/api/humanize", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_api_tools_endpoint(async_client):
    payload = {
        "text": "This is another test document that should be rewritten.",
        "tone": "formal",
        "locked_keywords": [],
        "tool": "rewrite",
    }
    response = await async_client.post("/api/tools", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["result"].strip()
    assert data["metadata"]["tone_applied"] == "formal"


@pytest.mark.asyncio
async def test_api_evaluate_endpoint(async_client):
    response = await async_client.post(
        "/api/evaluate",
        json={
            "original_text": "Acme Corp raised 40 million dollars in 2026.",
            "candidate_text": "Acme Corp raised 40 million dollars in 2026.",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["composite_score"] > 0.9
    assert "scores" in data


@pytest.mark.asyncio
async def test_api_translate_returns_400(async_client):
    response = await async_client.post(
        "/api/tools",
        json={
            "text": "This is a test document for the translate tool.",
            "tone": "general",
            "locked_keywords": [],
            "tool": "translate",
        },
    )
    assert response.status_code == 400
    assert "not available" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_guest_rate_limiting(async_client):
    from app.middleware.rate_limit import reset_guest_limits

    reset_guest_limits()
    payload = {
        "text": "Valid text exceeding minimum ten character length requirement.",
        "tone": "general",
        "locked_keywords": [],
        "tool": "grammar",
    }

    # 6 requests allowed
    for _ in range(6):
        resp = await async_client.post("/api/humanize", json=payload)
        assert resp.status_code == 200

    # 7th request must be rate limited (429)
    resp = await async_client.post("/api/humanize", json=payload)
    assert resp.status_code == 429
    data = resp.json()
    assert "limit reached" in data["detail"].lower()
