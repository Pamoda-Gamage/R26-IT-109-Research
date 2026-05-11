from __future__ import annotations

from typing import List, Dict, Any


def filter_available(providers: List[Dict[str, Any]], include_busy_for_high_urgency: bool = True, urgency: str = "normal") -> List[Dict[str, Any]]:
    available = []
    for p in providers:
        status = p.get("current_status", "offline")
        if status == "online" or (include_busy_for_high_urgency and urgency == "high" and status == "busy"):
            available.append(p)
    return available
