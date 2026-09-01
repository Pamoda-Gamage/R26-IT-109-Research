import math
from dataclasses import dataclass, field
from pathlib import Path

import networkx as nx
import osmnx as ox

EARTH_RADIUS_M = 6_371_000


@dataclass
class Edge:
    to: int
    length_m: float
    speed_kph: float


@dataclass
class RoadGraph:
    nodes: dict[int, tuple[float, float]] = field(default_factory=dict)
    adjacency: dict[int, list[Edge]] = field(default_factory=dict)


def haversine_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1 = math.radians(a[0]), math.radians(a[1])
    lat2, lon2 = math.radians(b[0]), math.radians(b[1])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(h))


def nearest_node(graph: RoadGraph, lat: float, lon: float) -> int:
    """Brute-force nearest-node lookup by haversine distance -- fine for the graph
    sizes here (a few hundred to a few thousand nodes); would want a spatial index
    (e.g. osmnx's built-in KDTree) if this ever needs to scale to a full city."""
    return min(graph.nodes, key=lambda node_id: haversine_m(graph.nodes[node_id], (lat, lon)))


def load_graph_from_networkx(g: nx.MultiDiGraph) -> RoadGraph:
    road_graph = RoadGraph()
    for node_id, data in g.nodes(data=True):
        road_graph.nodes[node_id] = (data["y"], data["x"])
        road_graph.adjacency[node_id] = []

    for u, v, data in g.edges(data=True):
        speed = data.get("speed_kph", 30.0)
        road_graph.adjacency[u].append(Edge(to=v, length_m=data["length"], speed_kph=speed))

    return road_graph


def load_graph(place: str, cache_path: Path) -> RoadGraph:
    """Extract a drivable graph for `place` via osmnx, caching to GraphML so this
    never re-hits the network on every process start."""
    if cache_path.exists():
        g = ox.load_graphml(cache_path)
    else:
        g = ox.graph_from_place(place, network_type="drive")
        g = ox.add_edge_speeds(g)
        g = ox.add_edge_travel_times(g)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        ox.save_graphml(g, cache_path)

    for _, _, data in g.edges(data=True):
        data["speed_kph"] = data.get("speed_kph", data.get("speed", 30.0))
    return load_graph_from_networkx(g)


def load_graph_from_point(center: tuple[float, float], dist_m: float, cache_path: Path) -> RoadGraph:
    """Like load_graph, but extracts a radius around a point instead of a whole named
    place -- much faster for a demo-scale area than fetching a full city."""
    if cache_path.exists():
        g = ox.load_graphml(cache_path)
    else:
        g = ox.graph_from_point(center, dist=dist_m, network_type="drive")
        g = ox.add_edge_speeds(g)
        g = ox.add_edge_travel_times(g)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        ox.save_graphml(g, cache_path)

    for _, _, data in g.edges(data=True):
        data["speed_kph"] = data.get("speed_kph", data.get("speed", 30.0))
    return load_graph_from_networkx(g)
