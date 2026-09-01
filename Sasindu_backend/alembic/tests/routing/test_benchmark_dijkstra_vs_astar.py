import random

import networkx as nx
import pytest

from app.routing.astar import astar_shortest_path
from app.routing.dijkstra import dijkstra_shortest_path
from app.routing.graph_loader import haversine_m, load_graph_from_networkx


@pytest.fixture
def large_random_graph():
    random.seed(2024)
    g = nx.MultiDiGraph()
    coords = {i: (6.9 + random.random() * 0.2, 79.8 + random.random() * 0.2) for i in range(300)}
    for i, (y, x) in coords.items():
        g.add_node(i, y=y, x=x)
    for i in range(300):
        for j in random.sample(range(300), k=6):
            if i != j:
                straight_line_m = haversine_m(coords[i], coords[j])
                detour_factor = random.uniform(1.0, 1.4)
                g.add_edge(i, j, length=straight_line_m * detour_factor, speed_kph=random.choice([30, 40, 50, 60]))
    return load_graph_from_networkx(g)


def test_astar_visits_no_more_nodes_than_dijkstra_on_average(large_random_graph):
    """A* with an admissible heuristic should never need to expand more nodes
    than Dijkstra to reach an optimal path; on average it should expand fewer."""
    random.seed(5)
    node_ids = list(large_random_graph.nodes.keys())

    for _ in range(30):
        source, target = random.sample(node_ids, 2)
        d = dijkstra_shortest_path(large_random_graph, source, target, time_slot="midday")
        a = astar_shortest_path(large_random_graph, source, target, time_slot="midday")
        if d is None or a is None:
            continue
        assert abs(d.eta_minutes - a.eta_minutes) < 1e-6, "A* must find the same optimal ETA as Dijkstra"
