import random

import networkx as nx
import pytest

from app.routing.dijkstra import dijkstra_shortest_path
from app.routing.graph_loader import load_graph_from_networkx


@pytest.fixture
def random_graph():
    random.seed(42)
    g = nx.MultiDiGraph()
    for i in range(60):
        g.add_node(i, y=6.9 + random.random() * 0.1, x=79.8 + random.random() * 0.1)
    for i in range(60):
        for j in random.sample(range(60), k=4):
            if i != j:
                g.add_edge(i, j, length=random.uniform(100, 2000), speed_kph=random.choice([30, 40, 50, 60]))
    return g


def test_dijkstra_matches_networkx_on_50_random_pairs(random_graph):
    road_graph = load_graph_from_networkx(random_graph)

    def nx_weight(u, v, data):
        d = min(data.values(), key=lambda e: e["length"])
        speed_m_per_min = d.get("speed_kph", 30.0) * 1000 / 60
        return d["length"] / speed_m_per_min

    random.seed(7)
    node_ids = list(road_graph.nodes.keys())
    mismatches = []
    checked = 0
    for _ in range(200):
        source, target = random.sample(node_ids, 2)
        try:
            nx_eta = nx.shortest_path_length(random_graph, source, target, weight=nx_weight)
        except nx.NetworkXNoPath:
            continue
        result = dijkstra_shortest_path(road_graph, source, target, time_slot="early_morning")
        assert result is not None, f"our dijkstra found no path {source}->{target} but networkx did"
        if abs(result.eta_minutes - nx_eta) > 1e-6:
            mismatches.append((source, target, result.eta_minutes, nx_eta))
        checked += 1
        if checked >= 50:
            break

    assert checked >= 50, "fixture graph too sparse to sample 50 connected pairs"
    assert not mismatches, f"ETA mismatches vs networkx oracle: {mismatches[:5]}"
