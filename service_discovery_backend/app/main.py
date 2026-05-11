from __future__ import annotations

from typing import List, Dict, Any

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from app.models.schemas import (
    IntentRequest,
    IntentResponse,
    MatchRequest,
    MatchResponse,
    ProviderRegistrationRequest,
    ProviderRegistrationResponse,
    VoiceLoginRequest,
    VoiceLoginResponse,
)
from app.ml.predictor import predictor
from app.services.database import init_db, list_providers, save_request, list_requests, create_or_partial_provider, get_provider_by_phone
from app.services.audio_features import extract_wav_features
from app.agents.context_agent import analyze_context
from app.agents.search_agent import retrieve_candidates
from app.agents.distance_agent import enrich_distance
from app.agents.availability_agent import filter_available
from app.agents.ranking_agent import rank_providers

app = FastAPI(
    title="Behaviour-Aware Multilingual Voice-Based Local Service Discovery API",
    version="1.0.0",
    description="Runnable research prototype backend for multilingual intent, urgency detection, and multi-agent service matching.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok", "service": "local-service-discovery-backend", "training_report": predictor.training_report}


@app.post("/api/analyze-intent", response_model=IntentResponse)
def analyze_intent(request: IntentRequest) -> Dict[str, Any]:
    analysis = predictor.predict(request.transcript, visual_hint=request.visual_hint)
    return analysis


@app.post("/api/match-service", response_model=MatchResponse)
def match_service(request: MatchRequest) -> Dict[str, Any]:
    analysis = predictor.predict(request.transcript, visual_hint=request.visual_hint)
    context = analyze_context(request.latitude, request.longitude, analysis["urgency"])
    candidates = retrieve_candidates(analysis["intent"])
    candidates = [enrich_distance(p, request.latitude, request.longitude) for p in candidates]
    available = filter_available(candidates, urgency=analysis["urgency"])
    ranked = rank_providers(available, analysis["urgency"])[:5]
    save_request(request.transcript, analysis["intent"], analysis["urgency"], request.latitude, request.longitude, analysis["success_probability"])
    return {
        "analysis": analysis,
        "context": context,
        "ranked_providers": ranked,
        "agent_trace": [
            {"agent": "Context Agent", "output": context},
            {"agent": "Search Agent", "output": f"Retrieved {len(candidates)} candidates for {analysis['intent']}"},
            {"agent": "Distance Agent", "output": "Calculated Haversine distance and ETA for every candidate."},
            {"agent": "Availability Agent", "output": f"Filtered to {len(available)} available provider(s)."},
            {"agent": "Ranking Agent", "output": f"Returned top {len(ranked)} provider(s) by trust, ETA, urgency, and fairness."},
        ],
    }


@app.post("/api/audio/analyze")
async def analyze_audio(file: UploadFile = File(...), transcript: str = "") -> Dict[str, Any]:
    content = await file.read()
    features = extract_wav_features(content)
    analysis = predictor.predict(transcript or file.filename, audio_features=features)
    return {"filename": file.filename, "audio_features": features, "analysis": analysis}


@app.get("/api/providers")
def providers(service_category: str | None = None) -> List[Dict[str, Any]]:
    return list_providers(service_category)


@app.get("/api/requests")
def requests(limit: int = 25) -> List[Dict[str, Any]]:
    return list_requests(limit)


@app.post("/api/providers/register-voice", response_model=ProviderRegistrationResponse)
def register_voice_provider(request: ProviderRegistrationRequest) -> Dict[str, Any]:
    required = ["first_name", "last_name", "service_category", "city"]
    data = request.model_dump()
    missing = [field for field in required if not data.get(field)]
    prompts = {
        "first_name": "Please speak your first name.",
        "last_name": "Please speak your last name.",
        "service_category": "Please say your service category, for example plumber, electrician, mechanic, cleaning, taxi, hospital, police, or fire.",
        "city": "Please say the city or area where you provide service.",
    }
    provider = create_or_partial_provider(data)
    next_prompt = prompts.get(missing[0]) if missing else "Registration completed. Your profile dashboard is ready."
    return {
        "status": "partial" if missing else "completed",
        "provider_id": provider.get("id"),
        "missing_fields": missing,
        "next_voice_prompt": next_prompt,
        "created_profile": provider,
    }


@app.post("/api/auth/voice-login", response_model=VoiceLoginResponse)
def voice_login(request: VoiceLoginRequest) -> Dict[str, Any]:
    provider = get_provider_by_phone(request.phone_number)
    if not provider:
        return {
            "authenticated": False,
            "method": "not_found",
            "provider": None,
            "message": "No account exists for this phone number. Please register first.",
        }
    spoken = request.spoken_name.lower().strip()
    full_name = f"{provider.get('first_name', '')} {provider.get('last_name', '')}".lower().strip()
    if provider.get("first_name", "").lower() in spoken or full_name in spoken:
        return {
            "authenticated": True,
            "method": "voice-name-confirmation",
            "provider": provider,
            "message": "Voice login accepted using spoken name confirmation. Full biometric matching can be connected later.",
        }
    return {
        "authenticated": False,
        "method": "otp-fallback-required",
        "provider": provider,
        "message": "Spoken name did not match the registered account. Use OTP fallback verification.",
    }
