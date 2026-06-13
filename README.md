# HD Map Pipeline

A lightweight HD map pipeline that ingests OpenStreetMap road network data, parses it into a directed lane graph, runs automated health checks to detect structural anomalies, and renders both static and interactive visualizations.

HD maps are a core dependency of autonomous vehicles — they encode lane geometry, topology, and road attributes at centimeter-level precision. This pipeline works at the road-network level using OpenStreetMap as the data source: given any location name, it fetches the road network, constructs a directed graph where nodes are intersections and edges are road segments, and automatically flags structural issues that would break downstream planners — isolated nodes, dead ends, missing lane data, disconnected subgraphs, turn restriction violations, and oneway topology errors.

The interactive output renders on real map tiles with clickable popups on every node and edge, making health issues spatially inspectable rather than just a console summary.

---

## Demo

**Interactive map — Zero Street, Fort Smith, AR**

![Demo](output/demo.gif)

> Open `output/graph.html` in a browser for the full interactive version with clickable nodes/edges and toggleable layers.

---

## Pipeline

```
Overpass API (OSM)
      │
      ▼
 src/ingest.py        ← fetch road network + turn restriction relations for any location
      │
      ▼
 src/parse.py         ← build NetworkX DiGraph with road class attributes, clip to bbox,
      │                  parse turn restriction relations (from/via/to members)
      ▼
 src/health.py        ← detect isolated nodes, dead ends, missing lane tags,
      │                  disconnected subgraphs, oneway conflicts, oneway sinks
      │
      ├──▶ src/visualize.py              → output/graph.png  (static, matplotlib)
      └──▶ src/visualize_interactive.py  → output/graph.html (interactive, Folium)
```

---

## Features

- **Location-aware** — pass any place name; Nominatim geocodes it to a bounding box automatically
- **Directed lane graph** — respects one-way streets; edge attributes include highway class, lane count, speed limit, road name
- **Road class hierarchy** — 8-tier OSM highway classification (motorway → other) stored as edge attribute; drives color coding in both outputs
- **Turn restriction parsing** — fetches OSM `restriction` relations; extracts `from_way`, `via_node`, `to_way`, and restriction type (`no_left_turn`, `only_straight_on`, etc.)
- **Oneway audit** — detects oneway tag conflicts (bidirectional edge where `oneway=yes`) and oneway sink nodes (reachable via oneway roads but no oneway exit)
- **6 health checks** — isolated nodes, dead ends, missing lane tags (grouped by road class tier), disconnected subgraphs, oneway conflicts, oneway sink nodes
- **Static PNG** — matplotlib render with road class color coding and dashed overlay for missing lane edges
- **Interactive HTML map** — Folium map on real OSM tiles with:
  - Roads color-coded by class tier (motorway=red, primary=orange, tertiary=blue, service=gray)
  - Click any road → name, highway type, road class, oneway, lane count, way ID
  - Click any node → type, in/out degree, coordinates
  - Purple markers for turn restriction via-nodes with restriction type in popup
  - Pink dashed edges for oneway conflicts; orange markers for oneway sinks
  - Toggleable layers per road class tier + all health check overlays
  - Legend with live health counts
- **Smart caching** — raw OSM JSON and bounding box cached locally; re-fetches only when location changes or `--force-fetch` is passed

---

## Quickstart

```bash
# clone and set up environment
git clone <repo-url>
cd hd-map-pipeline
conda create -n hd_map python=3.11
conda activate hd_map
pip install requests networkx matplotlib shapely folium

# run default — Zero Street, Fort Smith, AR
python main.py

# run on any location
python main.py --location "Zero Street, Fort Smith, Arkansas"
python main.py --location "Koregaon Park, Pune"
python main.py --location "Connaught Place, Delhi" --radius 1.0

# force re-fetch from Overpass API
python main.py --force-fetch

# skip interactive HTML (PNG only)
python main.py --no-interactive
```

---

## Project Structure

```
hd-map-pipeline/
├── src/
│   ├── ingest.py                ← Overpass API query + Nominatim geocoding
│   ├── parse.py                 ← OSM JSON → NetworkX DiGraph, road class assignment,
│   │                               bbox clipping, turn restriction parsing
│   ├── health.py                ← structural health checks on the graph
│   ├── visualize.py             ← static matplotlib PNG with road class color coding
│   └── visualize_interactive.py ← interactive Folium HTML map
├── output/
│   ├── graph.png                ← static map (generated)
│   ├── graph.html               ← interactive map (generated)
│   ├── raw_osm.json             ← cached OSM response (generated)
│   └── raw_bbox.json            ← cached bounding box + location (generated)
├── main.py                      ← full pipeline entrypoint
└── README.md
```

---

## Health Checks

| Check | What it detects | Method |
|---|---|---|
| Isolated nodes | Nodes with no edges | `nx.isolates(G)` |
| Dead ends | Nodes reachable but with no exit (in > 0, out = 0) | Degree scan |
| Missing lane tags | Edges where `lanes` attribute is absent, grouped by road class tier | Edge attribute scan |
| Disconnected subgraphs | More than one weakly connected component | `nx.weakly_connected_components(G)` |
| Oneway conflicts | Edge tagged `oneway=yes` where the reverse edge also exists in the graph | Bidirectional edge scan on oneway subset |
| Oneway sink nodes | Nodes with oneway in-edges but no oneway out-edges (routing dead-trap) | Degree scan on oneway subgraph |

---

## Road Class Tiers

| Tier | OSM Types | Color |
|---|---|---|
| 1–2 | motorway, trunk | Red `#e63946` |
| 3–4 | primary, secondary | Orange `#f4a261` |
| 5–6 | tertiary, residential | Blue `#457b9d` |
| 7–8 | service, unclassified, other | Gray `#adb5bd` |

Missing lane tags rendered as dashed edges at reduced opacity in both outputs.

---

## Sample Output — Zero Street, Fort Smith, AR

```
Graph: 1753 nodes, 4071 edges
Turn restrictions: 4
Health check results:
  Isolated nodes     : 2
  Dead ends          : 2
  Missing lane edges : 3681
  Disconnected       : True (5 components)
    class 3 (primary/secondary): 10 edges
    class 4 (primary/secondary): 77 edges
    class 5 (tertiary/residential): 87 edges
    class 6 (tertiary/residential): 242 edges
    class 7 (service/unclassified): 875 edges
    class 8 (other): 2390 edges
  Turn restriction breakdown:
    no_left_turn: 2
    no_right_turn: 1
    only_straight_on: 1
  Oneway conflicts   : 0
  Oneway sink nodes  : 16
```
