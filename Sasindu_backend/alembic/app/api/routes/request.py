import uuid
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select

from app.api.dependencies import get_adaptive_ranker
from app.availability.availability_agent import AvailabilityAgent
from app.context.context_agent import ContextAgent
from app.context.llm_client import LLMClient
from app.coordinator.graph import build_graph
from app.coordinator.state import new_pipeline_state
from app.db.models.provider import Provider
from app.db.models.request_log import RequestLog
from app.db.session import get_session, new_session
from app.ranking.weight_profiles import ARM_NAMES
from app.routing.distance_agent import DistanceAgent
from app.routing.graph_loader import load_graph_from_point, nearest_node
from app.search.bm25_index import BM25Index
from app.search.search_agent import SearchAgent
from app.search.vector_store import VectorStore

router = APIRouter()

_DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"
_GRAPH_CACHE = _DATA_DIR / "graphs" / "demo_city.graphml"
_CHROMA_DIR = str(_DATA_DIR / "chroma")

# Centroid of the seeded provider regions (see app/scripts/seed_providers.py REGIONS) --
# used both as the extraction center and the default request origin.
_COLOMBO_CENTER = (6.9271, 79.8612)
_REGION_CENTROIDS = {
    "colombo-01": (6.9344, 79.8428),
    "colombo-02": (6.9271, 79.8612),
    "dehiwala": (6.8500, 79.8667),
    "mount-lavinia": (6.8389, 79.8653),
    "kotte": (6.8905, 79.9021),
}


class RequestPayload(BaseModel):
    raw_text: str
    timestamp: str
    region: str


@router.post("/request")
async def submit_request(payload: RequestPayload):
    request_id = str(uuid.uuid4())
    state = new_pipeline_state(request_id, payload.raw_text, payload.timestamp, payload.region)

    compiled_graph = await _get_compiled_graph()
    final_state = await compiled_graph.ainvoke(state)

    ranked_ids = []
    for candidate in final_state["ranked"]:
        try:
            ranked_ids.append(uuid.UUID(candidate.provider_id))
        except ValueError:
            continue
    async with get_session() as session:
        session.add(
            RequestLog(
                id=uuid.UUID(request_id),
                raw_text=payload.raw_text,
                metadata_json={"trace": final_state["trace"], "chosen_arm": ARM_NAMES[final_state["chosen_arm_index"]]},
            )
        )
        await session.commit()

        providers_by_id = {}
        if ranked_ids:
            result = await session.execute(select(Provider).where(Provider.id.in_(ranked_ids)))
            providers_by_id = {str(p.id): p for p in result.scalars().all()}

    ranked_response = []
    for rank, candidate in enumerate(final_state["ranked"], start=1):
        provider = providers_by_id.get(candidate.provider_id)
        availability = final_state["availability"].get(candidate.provider_id)
        path = final_state["distances"].get(candidate.provider_id)
        ranked_response.append(
            {
                "provider_id": candidate.provider_id,
                "rank": rank,
                "score": candidate.score,
                "name": provider.name if provider else None,
                "service_type": provider.service_type if provider else None,
                "region": provider.region if provider else None,
                "rating": provider.rating if provider else None,
                "avatar_url": provider.avatar_url if provider else None,
                "phone": provider.phone if provider else None,
                "years_experience": provider.years_experience if provider else None,
                "bio": provider.profile_text if provider else None,
                "eta_minutes": path.eta_minutes if path else None,
                "distance_km": round(path.distance_m / 1000, 2) if path else None,
                "acceptance_probability": availability.acceptance_probability if availability else None,
                "status": availability.status if availability else None,
            }
        )

    return {
        "request_id": request_id,
        "ranked": ranked_response,
        "chosen_arm": ARM_NAMES[final_state["chosen_arm_index"]],
        "arm_index": final_state["chosen_arm_index"],
        "context_vector": final_state["context_vector"],
        "trace": final_state["trace"],
    }


_compiled_graph = None


async def _get_compiled_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = await _build_compiled_graph()
    return _compiled_graph


async def _build_compiled_graph():
    road_graph = load_graph_from_point(center=_COLOMBO_CENTER, dist_m=6000, cache_path=_GRAPH_CACHE)

    async with get_session() as session:
        result = await session.execute(select(Provider))
        providers = result.scalars().all()

    provider_lookup = {str(p.id): p for p in providers}
    provider_nodes = {str(p.id): nearest_node(road_graph, p.lat, p.lon) for p in providers}

    ids = list(provider_lookup.keys())
    texts = [p.profile_text for p in providers]
    metadatas = [{"service_type": p.service_type, "region": p.region} for p in providers]

    vector_store = VectorStore(persist_dir=_CHROMA_DIR, collection_name="providers")
    vector_store.upsert(ids, texts, metadatas)
    bm25_index = BM25Index()
    bm25_index.build(ids, texts)

    def source_node_resolver(state):
        center = _REGION_CENTROIDS.get(state["region"], _COLOMBO_CENTER)
        return nearest_node(road_graph, *center)

    return build_graph(
        context_agent=ContextAgent(llm_client=LLMClient()),
        search_agent=SearchAgent(vector_store=vector_store, bm25_index=bm25_index),
        distance_agent=DistanceAgent(graph=road_graph),
        availability_agent=AvailabilityAgent(),
        adaptive_ranker=get_adaptive_ranker(),
        provider_nodes=provider_nodes,
        source_node_resolver=source_node_resolver,
        session_factory=new_session,
        provider_lookup_factory=lambda: provider_lookup,
    )
