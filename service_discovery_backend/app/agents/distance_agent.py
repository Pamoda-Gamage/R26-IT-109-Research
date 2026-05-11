from __future__ import annotations

from math import radians, sin, cos, atan2, sqrt
from typing import Dict, Any


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return radius * c


def enrich_distance(provider: Dict[str, Any], user_lat: float | None, user_lon: float | None) -> Dict[str, Any]:
    if user_lat is None or user_lon is None:
        distance = 5.0
    else:
        distance = haversine_km(float(user_lat), float(user_lon), float(provider["latitude"]), float(provider["longitude"]))
    eta = max(5.0, distance / 28.0 * 60.0 + float(provider.get("response_speed_minutes", 20)) * 0.35)
    p = dict(provider)
    p["distance_km"] = round(distance, 2)
    p["eta_minutes"] = round(eta, 1)
    return p
