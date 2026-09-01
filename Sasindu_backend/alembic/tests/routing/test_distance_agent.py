import networkx as nx

from app.routing.distance_agent import DistanceAgent, ProviderLocation
from app.routing.graph_loader import load_graph_from_networkx


def _toy_graph():
    g = nx.MultiDiGraph()
    coords = {1: (6.93, 79.84), 2: (6.94, 79.85), 3: (6.95, 79.86), 4: (6.96, 79.87)}
    for n, (y, x) in coords.items():
        g.add_node(n, y=y, x=x)
    g.add_edge(1, 2, length=500, speed_kph=40)
    g.add_edge(1, 3, length=900, speed_kph=40)
    g.add_edge(1, 4, length=1400, speed_kph=40)
    return load_graph_from_networkx(g)


def test_score_candidates_returns_eta_per_provider():
    agent = DistanceAgent(graph=_toy_graph())
    providers = [
        ProviderLocation(provider_id="p2", lat=6.94, lon=79.85, node_id=2),
        ProviderLocation(provider_id="p3", lat=6.95, lon=79.86, node_id=3),
    ]
    results = agent.score_candidates(providers, source_node=1, time_slot="midday")
    assert set(results.keys()) == {"p2", "p3"}
    assert results["p2"].eta_minutes < results["p3"].eta_minutes
