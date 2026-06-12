import json
import os

from src.ingest import query_osm, save_raw, FORT_SMITH_DOWNTOWN
from src.parse import build_graph
from src.health import run_health_checks
from src.visualize import visualize

RAW_PATH = "output/raw_osm.json"


def main(force_fetch: bool = False):
    if not force_fetch and os.path.exists(RAW_PATH):
        print(f"Using cached data from {RAW_PATH}")
        with open(RAW_PATH) as f:
            data = json.load(f)
    else:
        data = query_osm(FORT_SMITH_DOWNTOWN)
        save_raw(data)

    G = build_graph(data)
    print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    issues = run_health_checks(G)
    print(f"Health check results:")
    print(f"  Isolated nodes     : {len(issues['isolated_nodes'])}")
    print(f"  Dead ends          : {len(issues['dead_ends'])}")
    print(f"  Missing lane edges : {len(issues['missing_lane_edges'])}")
    print(f"  Disconnected       : {issues['disconnected']} ({len(issues['components'])} components)")

    visualize(G, issues, FORT_SMITH_DOWNTOWN)


if __name__ == "__main__":
    main()
