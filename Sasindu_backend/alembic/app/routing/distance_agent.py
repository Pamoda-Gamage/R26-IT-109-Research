from dataclasses import dataclass
from typing import Literal

from app.routing.astar import astar_shortest_path
from app.routing.dijkstra import PathResult, dijkstra_shortest_path
from app.routing.graph_loader import RoadGraph


@dataclass
class ProviderLocation:
    provider_id: str
    lat: float
    lon: float
    node_id: int


class DistanceAgent:
    def __init__(self, graph: RoadGraph):
        self.graph = graph

    def score_candidates(
        self,
        providers: list[ProviderLocation],
        source_node: int,
        time_slot: str,
        algorithm: Literal["dijkstra", "astar"] = "dijkstra",
    ) -> dict[str, PathResult]:
        route_fn = dijkstra_shortest_path if algorithm == "dijkstra" else astar_shortest_path
        results: dict[str, PathResult] = {}
        for provider in providers:
            result = route_fn(self.graph, source_node, provider.node_id, time_slot)
            if result is not None:
                results[provider.provider_id] = result
        return results
