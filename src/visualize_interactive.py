import folium
import networkx as nx


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
    folium.map.Marker(
        location=center,
        popup=f"<b>{location}</b>",
        icon=folium.DivIcon(html=""),
    )

    dead_end_set = set(issues["dead_ends"])
    isolated_set = set(issues["isolated_nodes"])
    missing_lane_set = set(issues["missing_lane_edges"])

    # --- edge layers ---
    layer_normal_edges = folium.FeatureGroup(name="Normal edges", show=True)
    layer_missing_lanes = folium.FeatureGroup(name="Missing lane edges", show=True)

    for u, v, data in G.edges(data=True):
        u_data = G.nodes[u]
        v_data = G.nodes[v]
        coords = [[u_data["lat"], u_data["lon"]], [v_data["lat"], v_data["lon"]]]

        popup_html = f"""
        <b>{data.get('name') or 'Unnamed road'}</b><br>
        Highway: {data.get('highway') or '—'}<br>
        Oneway: {'Yes' if data.get('oneway') else 'No'}<br>
        Lanes: {data.get('lanes') or '<span style="color:red">missing</span>'}<br>
        Way ID: {data.get('way_id')}
        """
        popup = folium.Popup(popup_html, max_width=220)

        if (u, v) in missing_lane_set:
            folium.PolyLine(
                coords,
                color="#4a90d9",
                weight=2,
                opacity=0.8,
                dash_array="6 4",
                popup=popup,
            ).add_to(layer_missing_lanes)
        else:
            folium.PolyLine(
                coords,
                color="#888888",
                weight=1.5,
                opacity=0.6,
                popup=popup,
            ).add_to(layer_normal_edges)

    layer_normal_edges.add_to(m)
    layer_missing_lanes.add_to(m)

    # --- node layers ---
    layer_normal_nodes = folium.FeatureGroup(name="Normal nodes", show=True)
    layer_dead_ends = folium.FeatureGroup(name="Dead ends", show=True)
    layer_isolated = folium.FeatureGroup(name="Isolated nodes", show=True)

    for n in G.nodes:
        nd = G.nodes[n]
        lat, lon = nd["lat"], nd["lon"]

        if n in isolated_set:
            color, label, layer = "red", "Isolated", layer_isolated
            radius = 7
        elif n in dead_end_set:
            color, label, layer = "orange", "Dead end", layer_dead_ends
            radius = 6
        else:
            color, label, layer = "#555555", "Normal", layer_normal_nodes
            radius = 3

        popup_html = f"""
        <b>Node {n}</b><br>
        Type: {label}<br>
        In-degree: {G.in_degree(n)} | Out-degree: {G.out_degree(n)}<br>
        Lat: {lat:.6f}, Lon: {lon:.6f}
        """
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

    # --- legend ---
    legend_html = f"""
    <div style="position:fixed; bottom:30px; left:30px; z-index:1000;
                background:white; padding:12px 16px; border-radius:8px;
                border:1px solid #ccc; font-size:13px; line-height:1.8;">
        <b>{location}</b><br>
        <span style="color:#888">&#9644;</span> Normal edge<br>
        <span style="color:#4a90d9">&#9644;&#9644;</span> Missing lane tag ({len(missing_lane_set)})<br>
        <span style="color:#555">&#9679;</span> Normal node<br>
        <span style="color:orange">&#9679;</span> Dead end ({len(dead_end_set)})<br>
        <span style="color:red">&#9679;</span> Isolated ({len(isolated_set)})<br>
        <hr style="margin:6px 0">
        Components: {len(issues['components'])}
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    folium.LayerControl(collapsed=False).add_to(m)

    m.save(save_path)
    print(f"Interactive map saved to {save_path}")
