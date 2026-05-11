from __future__ import annotations

from datetime import datetime
from typing import Dict, Any


def analyze_context(latitude: float | None, longitude: float | None, urgency: str) -> Dict[str, Any]:
    hour = datetime.now().hour
    is_night = hour < 6 or hour >= 20
    radius = 25 if urgency == "high" else 15 if urgency == "moderate" else 10
    if is_night and urgency in {"moderate", "high"}:
        radius += 5
    return {
        "request_hour": hour,
        "is_night_request": is_night,
        "search_radius_km": radius,
        "latitude": latitude,
        "longitude": longitude,
        "urgency_priority": {"normal": 1, "moderate": 2, "high": 3}.get(urgency, 1),
    }
