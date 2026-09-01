import random

import networkx as nx
import pytest

from app.routing.astar import astar_shortest_path
from app.routing.dijkstra import dijkstra_shortest_path
from app.routing.graph_loader import haversine_m, load_graph_from_networkx


@pytest.fixture
def random_graph():
    """Edge length must be derived from real node coordinates (length = haversine * a
    detour factor >= 1.0), not sampled independently. A* haversine heuristic's
    admissibility relies on road distance never being shorter than straight-line
    distance; independently-random lengths can violate that and make A* legitimately
    diverge from Dijkstra, which is a broken fixture, not an algorithm bug."""
    random.seed(99)
    g = nx.MultiDiGraph()
    coords = {i: (6.9 + random.random() * 0.1, 79.8 + random.random() * 0.1) for i in range(60)}
    for i, (y, x) in coords.items():
        g.add_node(i, y=y, x=x)
    for i in range(60):
        for j in random.sample(range(60), k=4):
            if i != j:
                straight_line_m = haversine_m(coords[i], coords[j])
                detour_factor = random.uniform(1.0, 1.4)
                g.add_edge(i, j, length=straight_line_m * detour_factor, speed_kph=random.choice([30, 40, 50, 60]))
    return g


def test_astar_matches_dijkstra_eta_on_50_random_pairs(random_graph):
    """A* with an admissible heuristic must return the same optimal ETA as Dijkstra."""
    road_graph = load_graph_from_networkx(random_graph)
    random.seed(11)
    node_ids = list(road_graph.nodes.keys())
    checked, mismatches = 0, []
    for _ in range(200):
        source, target = random.sample(node_ids, 2)
        d_result = dijkstra_shortest_path(road_graph, source, target, time_slot="midday")
        if d_result is None:
            continue
        a_result = astar_shortest_path(road_graph, source, target, time_slot="midday")
        assert a_result is not None
        if abs(a_result.eta_minutes - d_result.eta_minutes) > 1e-6:
            mismatches.append((source, target, a_result.eta_minutes, d_result.eta_minutes))
        checked += 1
        if checked >= 50:
            break

    assert checked >= 50
    assert not mismatches, f"A* ETA diverged from Dijkstra oracle: {mismatches[:5]}"
