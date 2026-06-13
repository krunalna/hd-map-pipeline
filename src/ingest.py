import math
import requests
import json
import os

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
HEADERS = {"User-Agent": "hd-map-pipeline/1.0 (research project)"}

FORT_SMITH_DOWNTOWN = {
    "south": 35.3820,
    "west": -94.4300,
    "north": 35.3900,
    "east": -94.4200
}


def geocode_location(query: str, radius_km: float = 0.75) -> dict:
    """Convert a place name to a bounding box using Nominatim."""
    response = requests.get(
        NOMINATIM_URL,
        params={"q": query, "format": "json", "limit": 1},
        headers=HEADERS,
    )
    response.raise_for_status()
    results = response.json()
    if not results:
        raise ValueError(f"No results found for: {query!r}")

    lat = float(results[0]["lat"])
    lon = float(results[0]["lon"])
    print(f"Geocoded '{query}' → lat={lat:.4f}, lon={lon:.4f}")

    # convert km radius to degrees
    delta_lat = radius_km / 111.0
    delta_lon = radius_km / (111.0 * math.cos(math.radians(lat)))

    return {
        "south": round(lat - delta_lat, 6),
        "north": round(lat + delta_lat, 6),
        "west": round(lon - delta_lon, 6),
        "east": round(lon + delta_lon, 6),
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
    relation["type"="restriction"]({bbox['south']},{bbox['west']},{bbox['north']},{bbox['east']})->.restrictions;
    (.roads; .nodes; .restrictions;);
    out body qt;
    """

    print(f"Querying Overpass API for bounding box: {bbox}")
    response = requests.post(
        OVERPASS_URL,
        data={"data": overpass_query.strip()},
        headers=HEADERS,
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
    relations = [e for e in data["elements"] if e["type"] == "relation"]
    print(f"\nSummary:")
    print(f"  Nodes     : {len(nodes)}")
    print(f"  Ways      : {len(ways)}")
    print(f"  Relations : {len(relations)}")