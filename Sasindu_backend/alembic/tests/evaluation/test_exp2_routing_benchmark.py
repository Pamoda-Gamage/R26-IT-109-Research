import random

import networkx as nx

from app.routing.graph_loader import haversine_m, load_graph_from_networkx
from evaluation.experiments.exp2_routing_benchmark import run_experiment


def _sample_graph():
    random.seed(3)
    g = nx.MultiDiGraph()
    coords = {i: (6.9 + random.random() * 0.1, 79.8 + random.random() * 0.1) for i in range(100)}
    for i, (y, x) in coords.items():
        g.add_node(i, y=y, x=x)
    for i in range(100):
        for j in random.sample(range(100), k=5):
            if i != j:
                straight_line_m = haversine_m(coords[i], coords[j])
                detour_factor = random.uniform(1.0, 1.4)
                g.add_edge(i, j, length=straight_line_m * detour_factor, speed_kph=random.choice([30, 40, 50]))
    return load_graph_from_networkx(g)


def test_run_experiment_reports_both_algorithms_with_matching_eta():
    graph = _sample_graph()
    df = run_experiment(graph, seed=42, n_pairs=20)
    assert set(df["algorithm"].unique()) == {"dijkstra", "astar"}
    pivoted = df.pivot(index=["source", "target"], columns="algorithm", values="eta_minutes")
    assert (pivoted["dijkstra"] - pivoted["astar"]).abs().max() < 1e-6


def test_astar_never_expands_more_nodes_than_dijkstra_on_average():
    graph = _sample_graph()
    df = run_experiment(graph, seed=42, n_pairs=30)
    avg_expansions = df.groupby("algorithm")["nodes_expanded"].mean()
    assert avg_expansions["astar"] <= avg_expansions["dijkstra"]
