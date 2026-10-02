import pytest
from app.services.llm_service import llm_service


def test_clean_json_response_with_markdown_fence():
    raw = 'Here is your JSON:\n```json\n{"questions": [{"id": 1, "question": "What is RAM?"}]}\n```\nHope this helps!'
    parsed = llm_service.clean_json_response(raw)
    assert "questions" in parsed
    assert len(parsed["questions"]) == 1
    assert parsed["questions"][0]["question"] == "What is RAM?"


def test_clean_json_response_with_trailing_commas():
    raw = '{"name": "test", "items": [1, 2, ], }'
    parsed = llm_service.clean_json_response(raw)
    assert parsed["name"] == "test"
    assert parsed["items"] == [1, 2]


@pytest.mark.asyncio
async def test_generate_completion_offline_fallback():
    prompt = "Explain deadlocks"
    resp, provider = await llm_service.generate_completion(
        prompt=prompt, fallback_offline_fn=lambda: "Heuristic explanation of deadlocks"
    )
    assert resp == "Heuristic explanation of deadlocks"
    assert provider == "Local Heuristic Engine"


@pytest.mark.asyncio
async def test_provider_status_offline_by_default():
    status = await llm_service.check_provider_status()
    assert status["active_provider"] == "offline"
