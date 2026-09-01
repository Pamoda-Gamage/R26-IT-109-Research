from datetime import UTC, datetime

from app.context.context_agent import ContextAgent


class FakeLLMClient:
    def __init__(self, response: str):
        self._response = response

    async def classify_context(self, raw_text: str, metadata: dict) -> str:
        return self._response


async def test_infer_computes_time_slot_via_rules_not_llm():
    fake = FakeLLMClient('{"urgency": "normal", "constraints": [], "confidence": 0.8}')
    agent = ContextAgent(llm_client=fake)
    result = await agent.infer("need a plumber", datetime(2026, 1, 1, 18, 30, tzinfo=UTC), region="colombo-01")
    assert result.time_slot == "evening_peak"
    assert result.region == "colombo-01"


async def test_infer_uses_llm_for_urgency_and_constraints():
    fake = FakeLLMClient('{"urgency": "emergency", "constraints": ["burst pipe"], "confidence": 0.95}')
    agent = ContextAgent(llm_client=fake)
    result = await agent.infer("pipe burst, water everywhere!", datetime.now(UTC), region="colombo-01")
    assert result.urgency == "emergency"
    assert result.constraints == ["burst pipe"]


async def test_infer_falls_back_to_normal_on_malformed_llm_output():
    fake = FakeLLMClient("this is not json")
    agent = ContextAgent(llm_client=fake)
    result = await agent.infer("anything", datetime.now(UTC), region="colombo-01")
    assert result.urgency == "normal"
    assert result.constraints == []


async def test_infer_falls_back_to_normal_on_llm_exception():
    class ExplodingClient:
        async def classify_context(self, raw_text: str, metadata: dict) -> str:
            raise RuntimeError("API down")

    agent = ContextAgent(llm_client=ExplodingClient())
    result = await agent.infer("anything", datetime.now(UTC), region="colombo-01")
    assert result.urgency == "normal"
