# HD Map Pipeline

A lightweight HD map pipeline that ingests OpenStreetMap road network data, parses it into a directed lane graph, runs automated health checks to detect structural anomalies, and renders both static and interactive visualizations.

HD maps are a core dependency of autonomous vehicles — they encode lane geometry, topology, and road attributes at centimeter-level precision. This pipeline works at the road-network level using OpenStreetMap as the data source: given any location name, it fetches the road network, constructs a directed graph where nodes are intersections and edges are road segments, and automatically flags structural issues that would break downstream planners — isolated nodes, dead ends, missing lane data, and disconnected subgraphs.

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
 src/ingest.py        ← fetch road network for any location via Nominatim geocoding
      │
      ▼
 src/parse.py         ← build NetworkX directed graph, clip to bounding box
      │
      ▼
 src/health.py        ← detect isolated nodes, dead ends, missing lane tags, disconnected subgraphs
      │
      ├──▶ src/visualize.py              → output/graph.png  (static, matplotlib)
      └──▶ src/visualize_interactive.py  → output/graph.html (interactive, Folium)
```

---

## Features

- **Location-aware** — pass any place name; Nominatim geocodes it to a bounding box automatically
- **Directed lane graph** — respects one-way streets; edge attributes include highway class, lane count, speed limit, road name
- **4 health checks** — isolated nodes, dead ends, missing lane tags, disconnected subgraphs
- **Static PNG** — matplotlib render with color-coded health overlays
- **Interactive HTML map** — Folium map on real OSM tiles with:
  - Click any road → name, highway type, oneway, lane count
  - Click any node → type, in/out degree, coordinates
  - Toggle layers on/off (normal edges, missing lanes, dead ends, isolated nodes)
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
│   ├── parse.py                 ← OSM JSON → NetworkX DiGraph + bbox clipping
│   ├── health.py                ← structural health checks on the graph
│   ├── visualize.py             ← static matplotlib PNG
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
| Missing lane tags | Edges where `lanes` attribute is absent | Edge attribute scan |
| Disconnected subgraphs | More than one weakly connected component | `nx.weakly_connected_components(G)` |

---

## Sample Output — Zero Street, Fort Smith, AR

```
Graph: 366 nodes, 746 edges
Health check results:
  Isolated nodes     : 0
  Dead ends          : 0
  Missing lane edges : 706
  Disconnected       : True (7 components)
```
