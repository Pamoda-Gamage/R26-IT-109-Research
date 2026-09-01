import heapq
from dataclasses import dataclass

from app.routing.graph_loader import RoadGraph
from app.routing.traffic import traffic_multiplier


@dataclass
class PathResult:
    nodes: list[int]
    distance_m: float
    eta_minutes: float


def _edge_cost_minutes(length_m: float, speed_kph: float, time_slot: str) -> float:
    speed_m_per_min = speed_kph * 1000 / 60
    base_minutes = length_m / speed_m_per_min
    return base_minutes * traffic_multiplier(time_slot)


def dijkstra_shortest_path(graph: RoadGraph, source: int, target: int, time_slot: str) -> PathResult | None:
    """Priority-queue Dijkstra. Cost metric = time-dependent travel time (minutes),
    not raw distance, so the shortest path itself changes with time_slot."""
    dist: dict[int, float] = {source: 0.0}
    prev: dict[int, int] = {}
    visited: set[int] = set()
    heap: list[tuple[float, int]] = [(0.0, source)]

    while heap:
        cost, node = heapq.heappop(heap)
        if node in visited:
            continue
        visited.add(node)
        if node == target:
            break

        for edge in graph.adjacency.get(node, []):
            if edge.to in visited:
                continue
            edge_cost = _edge_cost_minutes(edge.length_m, edge.speed_kph, time_slot)
            new_cost = cost + edge_cost
            if new_cost < dist.get(edge.to, float("inf")):
                dist[edge.to] = new_cost
                prev[edge.to] = node
                heapq.heappush(heap, (new_cost, edge.to))

    if target not in dist:
        return None

    path = [target]
    while path[-1] != source:
        path.append(prev[path[-1]])
    path.reverse()

    distance_m = _reconstruct_distance_m(graph, path)
    return PathResult(nodes=path, distance_m=distance_m, eta_minutes=dist[target])


def _reconstruct_distance_m(graph: RoadGraph, path: list[int]) -> float:
    total = 0.0
    for u, v in zip(path, path[1:], strict=False):
        edge = next(e for e in graph.adjacency[u] if e.to == v)
        total += edge.length_m
    return total
