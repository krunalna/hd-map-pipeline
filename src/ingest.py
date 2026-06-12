import requests
import json
import os

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

FORT_SMITH_DOWNTOWN = {
    "south": 35.3820,
    "west": -94.4300,
    "north": 35.3900,
    "east": -94.4200
}

def query_osm(bbox: dict) -> dict:
    """
    Query Overpass API for road network within bounding box.
    Returns raw OSM JSON.
    """
    overpass_query = f"""
    [out:json][timeout:25];
    way["highway"]({bbox['south']},{bbox['west']},{bbox['north']},{bbox['east']})->.roads;
    node(w.roads)->.nodes;
    (.roads; .nodes;);
    out skel qt;
    """

    print(f"Querying Overpass API for bounding box: {bbox}")
    response = requests.post(
        OVERPASS_URL,
        data={"data": overpass_query.strip()},
        headers={"User-Agent": "hd-map-pipeline/1.0 (research project)"},
    )
    response.raise_for_status()

    data = response.json()
    print(f"Retrieved {len(data['elements'])} OSM elements")
    return data


def save_raw(data: dict, path: str = "output/raw_osm.json"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Raw OSM data saved to {path}")


if __name__ == "__main__":
    data = query_osm(FORT_SMITH_DOWNTOWN)
    save_raw(data)
    
    nodes = [e for e in data["elements"] if e["type"] == "node"]
    ways = [e for e in data["elements"] if e["type"] == "way"]
    print(f"\nSummary:")
    print(f"  Nodes : {len(nodes)}")
    print(f"  Ways  : {len(ways)}")