import heapq

from app.routing.dijkstra import PathResult, _edge_cost_minutes, _reconstruct_distance_m
from app.routing.graph_loader import RoadGraph, haversine_m

# Fastest plausible urban speed used to convert the haversine lower-bound distance
# into a lower-bound *time*, keeping the heuristic admissible (never overestimates).
MAX_PLAUSIBLE_SPEED_KPH = 60.0


def _heuristic_minutes(graph: RoadGraph, node: int, target: int, time_slot: str) -> float:
    dist_m = haversine_m(graph.nodes[node], graph.nodes[target])
    best_case_speed_m_per_min = MAX_PLAUSIBLE_SPEED_KPH * 1000 / 60
    return dist_m / best_case_speed_m_per_min


def astar_shortest_path(graph: RoadGraph, source: int, target: int, time_slot: str) -> PathResult | None:
    g_score: dict[int, float] = {source: 0.0}
    prev: dict[int, int] = {}
    visited: set[int] = set()
    h0 = _heuristic_minutes(graph, source, target, time_slot)
    heap: list[tuple[float, int]] = [(h0, source)]

    while heap:
        _, node = heapq.heappop(heap)
        if node in visited:
            continue
        visited.add(node)
        if node == target:
            break

        for edge in graph.adjacency.get(node, []):
            if edge.to in visited:
                continue
            tentative_g = g_score[node] + _edge_cost_minutes(edge.length_m, edge.speed_kph, time_slot)
            if tentative_g < g_score.get(edge.to, float("inf")):
                g_score[edge.to] = tentative_g
                prev[edge.to] = node
                f_score = tentative_g + _heuristic_minutes(graph, edge.to, target, time_slot)
                heapq.heappush(heap, (f_score, edge.to))

    if target not in g_score:
        return None

    path = [target]
    while path[-1] != source:
        path.append(prev[path[-1]])
    path.reverse()

    return PathResult(nodes=path, distance_m=_reconstruct_distance_m(graph, path), eta_minutes=g_score[target])
