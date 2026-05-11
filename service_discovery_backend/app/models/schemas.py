from __future__ import annotations

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class IntentRequest(BaseModel):
    transcript: str = Field(..., min_length=1, examples=["Hospital ekak near me urgent"])
    latitude: Optional[float] = Field(default=6.9271)
    longitude: Optional[float] = Field(default=79.8612)
    visual_hint: Optional[str] = Field(default=None, description="Optional image/context description such as 'pipe leak under sink'.")


class IntentResponse(BaseModel):
    transcript: str
    normalized_transcript: str
    intent: str
    urgency: str
    intent_probabilities: Dict[str, float]
    urgency_probabilities: Dict[str, float]
    keyword_hits: List[str]
    visual_adjustment: Optional[str]
    acoustic_adjustment: Optional[str]
    success_probability: float
    training_report: Dict[str, Any]


class MatchRequest(IntentRequest):
    pass


class Provider(BaseModel):
    id: int
    first_name: str
    last_name: str
    service_category: str
    city: str
    latitude: float
    longitude: float
    rating: float
    reliability: float
    response_speed_minutes: float
    urgent_task_success_rate: float
    current_status: str
    completed_jobs: int
    trust_score: float
    fairness_load_index: float
    phone_number: str
    profile_photo_url: Optional[str] = None


class RankedProvider(Provider):
    distance_km: float
    eta_minutes: float
    ranking_score: float
    ranking_explanation: str


class MatchResponse(BaseModel):
    analysis: IntentResponse
    context: Dict[str, Any]
    ranked_providers: List[RankedProvider]
    agent_trace: List[Dict[str, Any]]


class ProviderRegistrationRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    service_category: Optional[str] = None
    city: Optional[str] = None
    phone_number: str
    preferred_language: str = "English"
    voice_phrase: Optional[str] = None
    latitude: Optional[float] = 6.9271
    longitude: Optional[float] = 79.8612


class ProviderRegistrationResponse(BaseModel):
    status: str
    provider_id: Optional[int]
    missing_fields: List[str]
    next_voice_prompt: Optional[str]
    created_profile: Optional[Provider]


class VoiceLoginRequest(BaseModel):
    phone_number: str
    spoken_name: str
    voice_phrase: Optional[str] = None


class VoiceLoginResponse(BaseModel):
    authenticated: bool
    method: str
    provider: Optional[Provider]
    message: str
