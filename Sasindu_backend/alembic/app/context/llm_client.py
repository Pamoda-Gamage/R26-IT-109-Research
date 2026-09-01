from anthropic import AsyncAnthropic

from app.context.toon_serializer import to_toon

MODEL = "claude-haiku-4-5"  # explicit user choice for cost

SYSTEM_PROMPT = """You classify service requests. Given tabular request data, output ONLY a JSON object:
{"urgency": "emergency"|"normal", "constraints": [<short strings>], "confidence": <0-1 float>}
No prose, no markdown fences, JSON only."""


class LLMClient:
    def __init__(self, client: AsyncAnthropic | None = None, model: str = MODEL):
        self._client = client or AsyncAnthropic()
        self._model = model

    async def classify_context(self, raw_text: str, metadata: dict) -> str:
        rows = [{"field": "raw_text", "value": raw_text}] + [
            {"field": k, "value": str(v)} for k, v in metadata.items()
        ]
        prompt = to_toon(rows)
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        if response.stop_reason == "refusal":
            # Safety classifiers declined; ContextAgent treats empty/unparseable
            # output as a signal to fall back to normal urgency.
            return ""

        # Haiku 4.5 doesn't think by default, but scan defensively anyway --
        # this degrades gracefully for any model that does emit a thinking block.
        text_block = next((block for block in response.content if block.type == "text"), None)
        return text_block.text if text_block is not None else ""
