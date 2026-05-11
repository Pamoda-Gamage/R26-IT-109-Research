from __future__ import annotations

from typing import List, Dict, Any


def rank_providers(providers: List[Dict[str, Any]], urgency: str) -> List[Dict[str, Any]]:
    ranked: List[Dict[str, Any]] = []
    urgency_weight = {"normal": 0.10, "moderate": 0.15, "high": 0.25}.get(urgency, 0.10)
    for p in providers:
        rating = float(p.get("rating", 4.0)) / 5.0
        reliability = float(p.get("reliability", 0.7))
        urgent_success = float(p.get("urgent_task_success_rate", 0.6))
        trust = float(p.get("trust_score", 0.7))
        distance = float(p.get("distance_km", 5.0))
        fairness = max(0.0, 1.0 - float(p.get("fairness_load_index", 0.0)))
        eta = float(p.get("eta_minutes", 30.0))
        distance_score = max(0.0, 1.0 - min(distance, 50.0) / 50.0)
        eta_score = max(0.0, 1.0 - min(eta, 90.0) / 90.0)
        score = (
            0.20 * rating +
            0.18 * reliability +
            0.18 * trust +
            0.15 * distance_score +
            0.12 * eta_score +
            urgency_weight * urgent_success +
            0.08 * fairness
        )
        item = dict(p)
        item["ranking_score"] = round(score * 100, 2)
        item["ranking_explanation"] = (
            f"Ranked using rating={rating:.2f}, reliability={reliability:.2f}, trust={trust:.2f}, "
            f"distance={distance:.2f} km, ETA={eta:.1f} min, urgent-success={urgent_success:.2f}, "
            f"and fairness-opportunity={fairness:.2f}."
        )
        ranked.append(item)
    ranked.sort(key=lambda x: x["ranking_score"], reverse=True)
    return ranked
