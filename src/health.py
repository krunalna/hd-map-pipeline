import networkx as nx


def run_health_checks(G: nx.DiGraph, restrictions: list | None = None) -> dict:
    missing_lane_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get("lanes") is None]

    # group missing lane edges by road class — lower tier = higher severity
    missing_by_class: dict[int, list] = {}
    for u, v in missing_lane_edges:
        rc = G[u][v].get("road_class", 8)
        missing_by_class.setdefault(rc, []).append((u, v))

    restrictions = restrictions or []
    restriction_by_type: dict[str, list] = {}
    for r in restrictions:
        restriction_by_type.setdefault(r["type"], []).append(r)

    # oneway audit
    oneway_conflicts = [
        (u, v) for u, v, d in G.edges(data=True)
        if d.get("oneway") and G.has_edge(v, u)
    ]
    oneway_subgraph = nx.DiGraph()
    oneway_subgraph.add_edges_from(
        (u, v) for u, v, d in G.edges(data=True) if d.get("oneway")
    )
    oneway_sink_nodes = [
        n for n in oneway_subgraph.nodes
        if oneway_subgraph.in_degree(n) > 0 and oneway_subgraph.out_degree(n) == 0
    ]

    issues = {
        "isolated_nodes": list(nx.isolates(G)),
        "dead_ends": [n for n in G.nodes if G.out_degree(n) == 0 and G.in_degree(n) > 0],
        "missing_lane_edges": missing_lane_edges,
        "missing_lanes_by_class": missing_by_class,
        "components": list(nx.weakly_connected_components(G)),
        "turn_restrictions": restrictions,
        "turn_restrictions_by_type": restriction_by_type,
        "oneway_conflicts": oneway_conflicts,
        "oneway_sink_nodes": oneway_sink_nodes,
    }
    issues["disconnected"] = len(issues["components"]) > 1
    return issues


if __name__ == "__main__":
    import json
    from src.parse import build_graph

    with open("output/raw_osm.json") as f:
        data = json.load(f)

    G = build_graph(data)
    issues = run_health_checks(G)

    print(f"Isolated nodes     : {len(issues['isolated_nodes'])}")
    print(f"Dead ends          : {len(issues['dead_ends'])}")
    print(f"Missing lane edges : {len(issues['missing_lane_edges'])}")
    print(f"Components         : {len(issues['components'])}")
    print(f"Disconnected       : {issues['disconnected']}")
