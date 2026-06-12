import networkx as nx


def build_graph(osm_data: dict) -> nx.DiGraph:
    G = nx.DiGraph()

    nodes = {e["id"]: e for e in osm_data["elements"] if e["type"] == "node"}
    ways = [e for e in osm_data["elements"] if e["type"] == "way"]

    for node_id, node in nodes.items():
        G.add_node(node_id, lat=node["lat"], lon=node["lon"])

    for way in ways:
        tags = way.get("tags", {})
        oneway = tags.get("oneway", "no") == "yes"
        edge_attrs = {
            "highway": tags.get("highway"),
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


if __name__ == "__main__":
    import json

    with open("output/raw_osm.json") as f:
        data = json.load(f)

    G = build_graph(data)
    print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
