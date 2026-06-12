import matplotlib.pyplot as plt
import networkx as nx

CLASS_STYLE = {
    1: {"color": "#e63946", "width": 2.5},   # motorway/trunk
    2: {"color": "#e63946", "width": 2.5},
    3: {"color": "#f4a261", "width": 1.8},   # primary/secondary
    4: {"color": "#f4a261", "width": 1.8},
    5: {"color": "#457b9d", "width": 1.2},   # tertiary/residential
    6: {"color": "#457b9d", "width": 1.2},
    7: {"color": "#adb5bd", "width": 0.7},   # service/unclassified
    8: {"color": "#dee2e6", "width": 0.5},   # non-vehicle
}


def visualize(G: nx.DiGraph, issues: dict, location: str = "Road Network", save_path: str = "output/graph.png"):
    pos = {n: (G.nodes[n]["lon"], G.nodes[n]["lat"]) for n in G.nodes}

    missing_lane_set = set(issues["missing_lane_edges"])
    dead_end_set = set(issues["dead_ends"])
    isolated_set = set(issues["isolated_nodes"])
    normal_nodes = [n for n in G.nodes if n not in dead_end_set and n not in isolated_set]

    _, ax = plt.subplots(figsize=(14, 10))

    # edges grouped by road class
    by_class: dict[int, list] = {}
    for u, v in G.edges():
        rc = G[u][v].get("road_class", 8)
        by_class.setdefault(rc, []).append((u, v))

    for rc, edgelist in sorted(by_class.items(), reverse=True):
        style = CLASS_STYLE.get(rc, CLASS_STYLE[8])
        normal = [(u, v) for u, v in edgelist if (u, v) not in missing_lane_set]
        missing = [(u, v) for u, v in edgelist if (u, v) in missing_lane_set]
        if normal:
            nx.draw_networkx_edges(G, pos, edgelist=normal, ax=ax,
                                   edge_color=style["color"], width=style["width"],
                                   arrows=False, alpha=0.8)
        if missing:
            nx.draw_networkx_edges(G, pos, edgelist=missing, ax=ax,
                                   edge_color=style["color"], width=style["width"],
                                   arrows=False, alpha=0.4, style="dashed")

    # nodes
    nx.draw_networkx_nodes(G, pos, nodelist=normal_nodes, ax=ax,
                           node_color="#555555", node_size=4)
    if dead_end_set:
        nx.draw_networkx_nodes(G, pos, nodelist=list(dead_end_set), ax=ax,
                               node_color="orange", node_size=30)
    if isolated_set:
        nx.draw_networkx_nodes(G, pos, nodelist=list(isolated_set), ax=ax,
                               node_color="red", node_size=40)

    # legend
    legend_elements = [
        plt.Line2D([0], [0], color="#e63946", linewidth=2.5, label="Motorway / Trunk"),
        plt.Line2D([0], [0], color="#f4a261", linewidth=1.8, label="Primary / Secondary"),
        plt.Line2D([0], [0], color="#457b9d", linewidth=1.2, label="Tertiary / Residential"),
        plt.Line2D([0], [0], color="#adb5bd", linewidth=0.7, label="Service / Unclassified"),
        plt.Line2D([0], [0], color="#888888", linewidth=1.2, linestyle="dashed", label="Missing lane tag"),
        plt.scatter([], [], color="orange", s=50, label=f"Dead end ({len(dead_end_set)})"),
        plt.scatter([], [], color="red", s=60, label=f"Isolated ({len(isolated_set)})"),
    ]
    ax.legend(handles=legend_elements, loc="upper left", fontsize=8)

    title = (
        f"{location} — "
        f"{len(isolated_set)} isolated, "
        f"{len(dead_end_set)} dead ends, "
        f"{len(missing_lane_set)} edges missing lane data, "
        f"{len(issues['components'])} components"
    )
    ax.set_title(title, fontsize=10)
    ax.set_axis_off()

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved to {save_path}")


if __name__ == "__main__":
    import json
    from src.parse import build_graph, clip_to_bbox
    from src.health import run_health_checks
    from src.ingest import FORT_SMITH_DOWNTOWN

    with open("output/raw_osm.json") as f:
        data = json.load(f)

    G = clip_to_bbox(build_graph(data), FORT_SMITH_DOWNTOWN)
    issues = run_health_checks(G)
    visualize(G, issues, "Fort Smith Downtown")
