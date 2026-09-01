import json
import re
from typing import Literal

from pydantic import BaseModel, ValidationError

# Some models (Haiku 4.5 observed live) wrap JSON in a ```json ... ``` fence
# despite the system prompt saying not to -- strip it before parsing.
_FENCE_RE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)


class ContextResult(BaseModel):
    urgency: Literal["emergency", "normal"]
    constraints: list[str]
    confidence: float


def parse_llm_output(raw: str) -> ContextResult | None:
    stripped = raw.strip()
    match = _FENCE_RE.match(stripped)
    if match:
        stripped = match.group(1)

    try:
        data = json.loads(stripped)
    except json.JSONDecodeError:
        return None
    try:
        return ContextResult.model_validate(data)
    except ValidationError:
        return None
