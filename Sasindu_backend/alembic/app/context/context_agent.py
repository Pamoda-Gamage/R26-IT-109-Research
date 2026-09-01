from dataclasses import dataclass
from datetime import datetime

from app.context.schema import parse_llm_output
from app.routing.traffic import TIME_SLOTS


@dataclass
class ContextOutput:
    time_slot: str
    region: str
    urgency: str
    constraints: list[str]


def _time_slot_from_hour(hour: int) -> str:
    if 5 <= hour < 8:
        return "early_morning"
    if 8 <= hour < 10:
        return "morning_peak"
    if 10 <= hour < 17:
        return "midday"
    if 17 <= hour < 20:
        return "evening_peak"
    return "night"


class ContextAgent:
    def __init__(self, llm_client):
        self._llm_client = llm_client

    async def infer(self, raw_text: str, timestamp: datetime, region: str) -> ContextOutput:
        time_slot = _time_slot_from_hour(timestamp.hour)
        assert time_slot in TIME_SLOTS

        urgency, constraints = "normal", []
        try:
            raw_response = await self._llm_client.classify_context(raw_text, {"region": region, "time_slot": time_slot})
            parsed = parse_llm_output(raw_response)
            if parsed is not None:
                urgency, constraints = parsed.urgency, parsed.constraints
        except Exception:
            # Any LLM/network failure falls back to "normal" -- the pipeline must never crash here.
            pass

        return ContextOutput(time_slot=time_slot, region=region, urgency=urgency, constraints=constraints)
