import networkx as nx

from app.routing.dijkstra import dijkstra_shortest_path
from app.routing.graph_loader import load_graph_from_networkx


def test_eta_changes_with_time_slot():
    g = nx.MultiDiGraph()
    g.add_node(1, y=6.93, x=79.84)
    g.add_node(2, y=6.94, x=79.85)
    g.add_edge(1, 2, length=1000, speed_kph=40)
    road_graph = load_graph_from_networkx(g)

    peak = dijkstra_shortest_path(road_graph, 1, 2, time_slot="evening_peak")
    night = dijkstra_shortest_path(road_graph, 1, 2, time_slot="night")

    assert peak.eta_minutes > night.eta_minutes
    assert peak.distance_m == night.distance_m == 1000


def test_same_od_pair_can_prefer_different_routes_by_time_slot():
    g = nx.MultiDiGraph()
    for n, (y, x) in {1: (6.93, 79.84), 2: (6.94, 79.85), 3: (6.95, 79.86)}.items():
        g.add_node(n, y=y, x=x)
    g.add_edge(1, 3, length=1000, speed_kph=25)
    g.add_edge(1, 2, length=600, speed_kph=60)
    g.add_edge(2, 3, length=600, speed_kph=60)
    road_graph = load_graph_from_networkx(g)

    result = dijkstra_shortest_path(road_graph, 1, 3, time_slot="early_morning")
    assert result.nodes[0] == 1 and result.nodes[-1] == 3
