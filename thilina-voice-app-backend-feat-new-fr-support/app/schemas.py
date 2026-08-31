from pydantic import BaseModel
from typing import Optional


class CreateChatRequest(BaseModel):
    user_id: str
    title: Optional[str] = None


class SendTextRequest(BaseModel):
    # LLM primary-provider hint: "auto" (default), "gemini", or "openai".
    # Anything else (incl. legacy ids) is treated as "auto" server-side.
    text: str
    model: str = "auto"