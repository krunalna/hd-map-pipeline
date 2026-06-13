import networkx as nx

ROAD_CLASS = {
    "motorway": 1,       "motorway_link": 1,
    "trunk": 2,          "trunk_link": 2,
    "primary": 3,        "primary_link": 3,
    "secondary": 4,      "secondary_link": 4,
    "tertiary": 5,       "tertiary_link": 5,
    "residential": 6,    "living_street": 6,
    "service": 7,        "unclassified": 7,
}


def build_graph(osm_data: dict) -> nx.DiGraph:
    G = nx.DiGraph()

    nodes = {e["id"]: e for e in osm_data["elements"] if e["type"] == "node"}
    ways = [e for e in osm_data["elements"] if e["type"] == "way"]

    for node_id, node in nodes.items():
        G.add_node(node_id, lat=node["lat"], lon=node["lon"])

    for way in ways:
        tags = way.get("tags", {})
        oneway = tags.get("oneway", "no") == "yes"
        highway = tags.get("highway")
        edge_attrs = {
            "highway": highway,
            "road_class": ROAD_CLASS.get(highway, 8),
            "lanes": tags.get("lanes"),
            "name": tags.get("name"),
            "maxspeed": tags.get("maxspeed"),
            "oneway": oneway,
            "way_id": way["id"],
        }
        node_ids = way["nodes"]
        for u, v in zip(node_ids[:-1], node_ids[1:]):
            G.add_edge(u, v, **edge_attrs)
            if not oneway:
                G.add_edge(v, u, **edge_attrs)

    return G


def parse_restrictions(osm_data: dict) -> list[dict]:
    """Extract turn restriction relations from raw OSM data."""
    restrictions = []
    for el in osm_data["elements"]:
        if el["type"] != "relation":
            continue
        tags = el.get("tags", {})
        if tags.get("type") != "restriction":
            continue

        members = el.get("members", [])
        from_way = next((m["ref"] for m in members if m["role"] == "from" and m["type"] == "way"), None)
        to_way = next((m["ref"] for m in members if m["role"] == "to" and m["type"] == "way"), None)
        via_node = next((m["ref"] for m in members if m["role"] == "via" and m["type"] == "node"), None)

        restriction_type = tags.get("restriction") or tags.get("restriction:conditional", "unknown")

        if from_way and to_way:
            restrictions.append({
                "relation_id": el["id"],
                "from_way": from_way,
                "via_node": via_node,
                "to_way": to_way,
                "type": restriction_type,
            })
    return restrictions


def clip_to_bbox(G: nx.DiGraph, bbox: dict) -> nx.DiGraph:
    in_bounds = {
        n for n in G.nodes
        if bbox["south"] <= G.nodes[n]["lat"] <= bbox["north"]
        and bbox["west"] <= G.nodes[n]["lon"] <= bbox["east"]
    }
    return G.subgraph(in_bounds).copy()


if __name__ == "__main__":
    import json

    with open("output/raw_osm.json") as f:
        data = json.load(f)

    G = build_graph(data)
    print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
