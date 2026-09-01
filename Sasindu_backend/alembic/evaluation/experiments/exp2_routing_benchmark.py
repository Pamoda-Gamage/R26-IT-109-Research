import heapq
import random
import time
from pathlib import Path

import pandas as pd

from app.routing.astar import _heuristic_minutes
from app.routing.dijkstra import _edge_cost_minutes, dijkstra_shortest_path
from app.routing.graph_loader import RoadGraph, load_graph_from_point
from evaluation.stats import bootstrap_ci


def _count_expansions_dijkstra(graph: RoadGraph, source: int, target: int, time_slot: str) -> int:
    dist = {source: 0.0}
    visited: set[int] = set()
    heap: list[tuple[float, int]] = [(0.0, source)]
    expansions = 0
    while heap:
        cost, node = heapq.heappop(heap)
        if node in visited:
            continue
        visited.add(node)
        expansions += 1
        if node == target:
            break
        for edge in graph.adjacency.get(node, []):
            if edge.to in visited:
                continue
            new_cost = cost + _edge_cost_minutes(edge.length_m, edge.speed_kph, time_slot)
            if new_cost < dist.get(edge.to, float("inf")):
                dist[edge.to] = new_cost
                heapq.heappush(heap, (new_cost, edge.to))
    return expansions


def _count_expansions_astar(graph: RoadGraph, source: int, target: int, time_slot: str) -> int:
    g_score = {source: 0.0}
    visited: set[int] = set()
    heap: list[tuple[float, int]] = [(_heuristic_minutes(graph, source, target, time_slot), source)]
    expansions = 0
    while heap:
        _, node = heapq.heappop(heap)
        if node in visited:
            continue
        visited.add(node)
        expansions += 1
        if node == target:
            break
        for edge in graph.adjacency.get(node, []):
            if edge.to in visited:
                continue
            tentative = g_score[node] + _edge_cost_minutes(edge.length_m, edge.speed_kph, time_slot)
            if tentative < g_score.get(edge.to, float("inf")):
                g_score[edge.to] = tentative
                heapq.heappush(heap, (tentative + _heuristic_minutes(graph, edge.to, target, time_slot), edge.to))
    return expansions


def run_experiment(graph: RoadGraph, seed: int, n_pairs: int = 50) -> pd.DataFrame:
    from app.routing.astar import astar_shortest_path

    rng = random.Random(seed)
    node_ids = list(graph.nodes.keys())
    rows = []
    checked, attempts = 0, 0
    while checked < n_pairs and attempts < n_pairs * 10:
        attempts += 1
        source, target = rng.sample(node_ids, 2)
        d_result = dijkstra_shortest_path(graph, source, target, time_slot="midday")
        if d_result is None:
            continue
        a_result = astar_shortest_path(graph, source, target, time_slot="midday")

        t0 = time.perf_counter()
        dijkstra_shortest_path(graph, source, target, time_slot="midday")
        d_runtime_ms = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        astar_shortest_path(graph, source, target, time_slot="midday")
        a_runtime_ms = (time.perf_counter() - t0) * 1000

        rows.append(
            {
                "algorithm": "dijkstra",
                "source": source,
                "target": target,
                "runtime_ms": d_runtime_ms,
                "nodes_expanded": _count_expansions_dijkstra(graph, source, target, "midday"),
                "eta_minutes": d_result.eta_minutes,
            }
        )
        rows.append(
            {
                "algorithm": "astar",
                "source": source,
                "target": target,
                "runtime_ms": a_runtime_ms,
                "nodes_expanded": _count_expansions_astar(graph, source, target, "midday"),
                "eta_minutes": a_result.eta_minutes,
            }
        )
        checked += 1

    return pd.DataFrame(rows)


def main(seed: int = 42) -> None:
    cache_path = Path(__file__).parent.parent.parent / "data" / "graphs" / "demo_city.graphml"
    graph = load_graph_from_point(center=(6.9271, 79.8612), dist_m=6000, cache_path=cache_path)

    df = run_experiment(graph, seed=seed, n_pairs=50)
    out_dir = Path(__file__).parent.parent / "results"
    out_dir.mkdir(exist_ok=True)
    df.to_csv(out_dir / "exp2_routing_benchmark.csv", index=False)

    summary = df.groupby("algorithm")[["runtime_ms", "nodes_expanded"]].mean()
    print(summary)
    for algorithm in ["dijkstra", "astar"]:
        runtimes = df[df.algorithm == algorithm]["runtime_ms"].tolist()
        mean, lo, hi = bootstrap_ci(runtimes, seed=seed)
        print(f"{algorithm}: mean_runtime_ms={mean:.3f} CI=[{lo:.3f},{hi:.3f}]")


if __name__ == "__main__":
    main()
