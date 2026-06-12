import argparse
import json
import os

from src.ingest import query_osm, save_raw, geocode_location, FORT_SMITH_DOWNTOWN
from src.parse import build_graph, clip_to_bbox
from src.health import run_health_checks
from src.visualize import visualize
from src.visualize_interactive import visualize_interactive

RAW_PATH = "output/raw_osm.json"
BBOX_PATH = "output/raw_bbox.json"


def main():
    parser = argparse.ArgumentParser(description="HD Map Pipeline")
    parser.add_argument("--location", type=str, default=None,
                        help="Place name to geocode (e.g. 'BT Kawde Road, Pune')")
    parser.add_argument("--radius", type=float, default=0.75,
                        help="Bounding box radius in km around geocoded point (default: 0.75)")
    parser.add_argument("--force-fetch", action="store_true",
                        help="Re-fetch from Overpass even if cache exists")
    parser.add_argument("--no-interactive", action="store_true",
                        help="Skip interactive HTML map, generate PNG only")
    args = parser.parse_args()

    if args.location:
        bbox = geocode_location(args.location, radius_km=args.radius)
        location = args.location
        force_fetch = True
    else:
        force_fetch = args.force_fetch
        if not force_fetch and os.path.exists(BBOX_PATH):
            with open(BBOX_PATH) as f:
                cached = json.load(f)
            bbox = cached["bbox"]
            location = cached["location"]
        else:
            bbox = FORT_SMITH_DOWNTOWN
            location = "Fort Smith Downtown"

    if not force_fetch and os.path.exists(RAW_PATH):
        print(f"Using cached data from {RAW_PATH}")
        with open(RAW_PATH) as f:
            data = json.load(f)
    else:
        data = query_osm(bbox)
        save_raw(data)
        os.makedirs("output", exist_ok=True)
        with open(BBOX_PATH, "w") as f:
            json.dump({"bbox": bbox, "location": location}, f, indent=2)

    G = clip_to_bbox(build_graph(data), bbox)
    print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    issues = run_health_checks(G)
    print(f"Health check results:")
    print(f"  Isolated nodes     : {len(issues['isolated_nodes'])}")
    print(f"  Dead ends          : {len(issues['dead_ends'])}")
    print(f"  Missing lane edges : {len(issues['missing_lane_edges'])}")
    print(f"  Disconnected       : {issues['disconnected']} ({len(issues['components'])} components)")
    class_labels = {1: "motorway/trunk", 2: "motorway/trunk", 3: "primary/secondary",
                    4: "primary/secondary", 5: "tertiary/residential", 6: "tertiary/residential",
                    7: "service/unclassified", 8: "other"}
    for rc in sorted(issues["missing_lanes_by_class"]):
        count = len(issues["missing_lanes_by_class"][rc])
        print(f"    class {rc} ({class_labels.get(rc, 'other')}): {count} edges")

    visualize(G, issues, location)
    if not args.no_interactive:
        visualize_interactive(G, issues, location)


if __name__ == "__main__":
    main()
