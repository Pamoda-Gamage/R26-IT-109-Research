from __future__ import annotations

from typing import List, Dict, Any
from app.services.database import list_providers


def retrieve_candidates(intent: str) -> List[Dict[str, Any]]:
    return list_providers(intent)
