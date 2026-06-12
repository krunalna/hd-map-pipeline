import matplotlib.pyplot as plt
import networkx as nx


def visualize(G: nx.DiGraph, issues: dict, bbox: dict, save_path: str = "output/graph.png"):
    in_bounds = {
        n for n in G.nodes
        if bbox["south"] <= G.nodes[n]["lat"] <= bbox["north"]
        and bbox["west"] <= G.nodes[n]["lon"] <= bbox["east"]
    }
    G = G.subgraph(in_bounds)
    pos = {n: (G.nodes[n]["lon"], G.nodes[n]["lat"]) for n in G.nodes}

    missing_lane_edges = {(u, v) for u, v in issues["missing_lane_edges"] if u in pos and v in pos}
    normal_edges = [(u, v) for u, v in G.edges() if (u, v) not in missing_lane_edges]

    dead_end_set = set(issues["dead_ends"]) & in_bounds
    isolated_set = set(issues["isolated_nodes"]) & in_bounds
    normal_nodes = [n for n in G.nodes if n not in dead_end_set and n not in isolated_set]

    _, ax = plt.subplots(figsize=(14, 10))

    # edges — base layer
    nx.draw_networkx_edges(G, pos, edgelist=normal_edges, ax=ax,
                           edge_color="#cccccc", width=0.5, arrows=False)
    nx.draw_networkx_edges(G, pos, edgelist=list(missing_lane_edges), ax=ax,
                           edge_color="#4a90d9", width=0.8, style="dashed", arrows=False)

    # nodes — overlay layers
    nx.draw_networkx_nodes(G, pos, nodelist=normal_nodes, ax=ax,
                           node_color="#888888", node_size=5)
    if dead_end_set:
        nx.draw_networkx_nodes(G, pos, nodelist=list(dead_end_set), ax=ax,
                               node_color="orange", node_size=30)
    if isolated_set:
        nx.draw_networkx_nodes(G, pos, nodelist=list(isolated_set), ax=ax,
                               node_color="red", node_size=40)

    # legend
    legend_elements = [
        plt.Line2D([0], [0], color="#cccccc", linewidth=1.5, label="Normal edge"),
        plt.Line2D([0], [0], color="#4a90d9", linewidth=1.5, linestyle="dashed", label="Missing lane tag"),
        plt.scatter([], [], color="#888888", s=15, label="Normal node"),
        plt.scatter([], [], color="orange", s=50, label=f"Dead end ({len(dead_end_set)})"),
        plt.scatter([], [], color="red", s=60, label=f"Isolated ({len(isolated_set)})"),
    ]
    ax.legend(handles=legend_elements, loc="upper left", fontsize=8)

    title = (
        f"Fort Smith Downtown — "
        f"{len(isolated_set)} isolated, "
        f"{len(dead_end_set)} dead ends, "
        f"{len(missing_lane_edges)} edges missing lane data, "
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
    from src.parse import build_graph
    from src.health import run_health_checks

    with open("output/raw_osm.json") as f:
        data = json.load(f)

    from src.ingest import FORT_SMITH_DOWNTOWN
    G = build_graph(data)
    issues = run_health_checks(G)
    visualize(G, issues, FORT_SMITH_DOWNTOWN)
