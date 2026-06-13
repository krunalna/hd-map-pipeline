import folium
import networkx as nx

CLASS_COLOR = {
    1: "#e63946", 2: "#e63946",   # motorway / trunk
    3: "#f4a261", 4: "#f4a261",   # primary / secondary
    5: "#457b9d", 6: "#457b9d",   # tertiary / residential
    7: "#adb5bd", 8: "#dee2e6",   # service / non-vehicle
}
CLASS_WEIGHT = {1: 5, 2: 5, 3: 4, 4: 4, 5: 3, 6: 3, 7: 2, 8: 1}
CLASS_LABEL = {
    1: "Motorway / Trunk", 2: "Motorway / Trunk",
    3: "Primary / Secondary", 4: "Primary / Secondary",
    5: "Tertiary / Residential", 6: "Tertiary / Residential",
    7: "Service / Unclassified", 8: "Other",
}


def visualize_interactive(
    G: nx.DiGraph,
    issues: dict,
    location: str = "Road Network",
    save_path: str = "output/graph.html",
):
    if G.number_of_nodes() == 0:
        print("Empty graph — skipping interactive visualization")
        return

    lats = [G.nodes[n]["lat"] for n in G.nodes]
    lons = [G.nodes[n]["lon"] for n in G.nodes]
    center = [sum(lats) / len(lats), sum(lons) / len(lons)]

    m = folium.Map(location=center, zoom_start=15, tiles="OpenStreetMap")

    dead_end_set = set(issues["dead_ends"])
    isolated_set = set(issues["isolated_nodes"])
    missing_lane_set = set(issues["missing_lane_edges"])

    # --- edge layers (one per road class tier) ---
    class_layers = {
        (1, 2): folium.FeatureGroup(name="Motorway / Trunk", show=True),
        (3, 4): folium.FeatureGroup(name="Primary / Secondary", show=True),
        (5, 6): folium.FeatureGroup(name="Tertiary / Residential", show=True),
        (7, 8): folium.FeatureGroup(name="Service / Other", show=True),
    }

    def get_layer(rc):
        for key, layer in class_layers.items():
            if rc in key:
                return layer
        return class_layers[(7, 8)]

    for u, v, data in G.edges(data=True):
        rc = data.get("road_class", 8)
        color = CLASS_COLOR.get(rc, "#dee2e6")
        weight = CLASS_WEIGHT.get(rc, 1)
        is_missing = (u, v) in missing_lane_set

        popup_html = (
            f"<b>{data.get('name') or 'Unnamed road'}</b><br>"
            f"Highway: {data.get('highway') or '—'}<br>"
            f"Class: {CLASS_LABEL.get(rc, 'Other')}<br>"
            f"Oneway: {'Yes' if data.get('oneway') else 'No'}<br>"
            f"Lanes: {data.get('lanes') or '<span style=color:red>missing</span>'}<br>"
            f"Max speed: {data.get('maxspeed') or '—'}<br>"
            f"Way ID: {data.get('way_id')}"
        )

        folium.PolyLine(
            [[G.nodes[u]["lat"], G.nodes[u]["lon"]], [G.nodes[v]["lat"], G.nodes[v]["lon"]]],
            color=color,
            weight=weight,
            opacity=0.5 if is_missing else 0.85,
            dash_array="6 4" if is_missing else None,
            popup=folium.Popup(popup_html, max_width=240),
            tooltip=data.get("name") or data.get("highway") or "road",
        ).add_to(get_layer(rc))

    for layer in class_layers.values():
        layer.add_to(m)

    # --- node layers ---
    layer_normal_nodes = folium.FeatureGroup(name="Normal nodes", show=False)
    layer_dead_ends = folium.FeatureGroup(name="Dead ends", show=True)
    layer_isolated = folium.FeatureGroup(name="Isolated nodes", show=True)

    for n in G.nodes:
        nd = G.nodes[n]
        lat, lon = nd["lat"], nd["lon"]

        if n in isolated_set:
            color, label, layer, radius = "red", "Isolated", layer_isolated, 7
        elif n in dead_end_set:
            color, label, layer, radius = "orange", "Dead end", layer_dead_ends, 6
        else:
            color, label, layer, radius = "#555555", "Normal", layer_normal_nodes, 3

        popup_html = (
            f"<b>Node {n}</b><br>"
            f"Type: {label}<br>"
            f"In-degree: {G.in_degree(n)} | Out-degree: {G.out_degree(n)}<br>"
            f"Lat: {lat:.6f}, Lon: {lon:.6f}"
        )
        folium.CircleMarker(
            location=[lat, lon],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.85,
            popup=folium.Popup(popup_html, max_width=200),
        ).add_to(layer)

    layer_normal_nodes.add_to(m)
    layer_dead_ends.add_to(m)
    layer_isolated.add_to(m)

    # --- turn restriction via nodes ---
    layer_restrictions = folium.FeatureGroup(name="Turn restrictions", show=True)
    for r in issues.get("turn_restrictions", []):
        via = r["via_node"]
        if via is None or via not in G.nodes:
            continue
        nd = G.nodes[via]
        popup_html = (
            f"<b>Turn Restriction</b><br>"
            f"Type: <b>{r['type']}</b><br>"
            f"From way: {r['from_way']}<br>"
            f"To way: {r['to_way']}<br>"
            f"Relation ID: {r['relation_id']}"
        )
        folium.CircleMarker(
            location=[nd["lat"], nd["lon"]],
            radius=8,
            color="#6a0dad",
            fill=True,
            fill_color="#6a0dad",
            fill_opacity=0.85,
            popup=folium.Popup(popup_html, max_width=220),
            tooltip=r["type"],
        ).add_to(layer_restrictions)
    layer_restrictions.add_to(m)

    # --- legend ---
    legend_html = f"""
    <div style="position:fixed; bottom:30px; left:30px; z-index:1000;
                background:white; padding:12px 16px; border-radius:8px;
                border:1px solid #ccc; font-size:12px; line-height:2;">
        <b>{location}</b><br>
        <span style="color:#e63946; font-size:16px">&#9644;</span> Motorway / Trunk<br>
        <span style="color:#f4a261; font-size:16px">&#9644;</span> Primary / Secondary<br>
        <span style="color:#457b9d; font-size:16px">&#9644;</span> Tertiary / Residential<br>
        <span style="color:#adb5bd; font-size:16px">&#9644;</span> Service / Other<br>
        <span style="color:#888; font-size:10px">&#9644; &#9644;</span> Missing lane tag<br>
        <span style="color:orange">&#9679;</span> Dead end ({len(dead_end_set)})<br>
        <span style="color:red">&#9679;</span> Isolated ({len(isolated_set)})<br>
        <span style="color:#6a0dad">&#9679;</span> Turn restriction ({len(issues.get('turn_restrictions', []))})<br>
        <hr style="margin:4px 0">
        Components: {len(issues['components'])}
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    folium.LayerControl(collapsed=False).add_to(m)

    m.save(save_path)
    print(f"Interactive map saved to {save_path}")
