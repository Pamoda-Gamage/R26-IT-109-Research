import networkx as nx
import pytest

from app.routing.graph_loader import load_graph_from_networkx


@pytest.fixture
def toy_graph():
    g = nx.MultiDiGraph()
    g.add_node(1, y=6.93, x=79.84)
    g.add_node(2, y=6.94, x=79.85)
    g.add_node(3, y=6.95, x=79.86)
    g.add_edge(1, 2, length=500, speed_kph=40)
    g.add_edge(2, 3, length=800, speed_kph=30)
    g.add_edge(1, 3, length=1500, speed_kph=50)
    return g


def test_load_graph_builds_adjacency_list(toy_graph):
    road_graph = load_graph_from_networkx(toy_graph)
    assert road_graph.nodes[1] == (6.93, 79.84)
    assert len(road_graph.adjacency[1]) == 2
    edge_to_2 = next(e for e in road_graph.adjacency[1] if e.to == 2)
    assert edge_to_2.length_m == 500
    assert edge_to_2.speed_kph == 40
