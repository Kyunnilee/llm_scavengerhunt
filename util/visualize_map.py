# -*- coding:utf-8 -*-

import folium
import networkx as nx
import matplotlib.pyplot as plt
import json
from typing import *


def build_graph_networkx(nodes: dict, edges: dict):
    '''
    Builds a graph using NetworkX.

    Args:
        nodes (dict): A dictionary of node IDs as keys and (latitude, longitude) tuples as values.
        edges (list): A list of edge tuples, where each tuple represents a connection between two nodes.

    Returns:
        G (networkx.Graph): A NetworkX graph with nodes positioned based on latitude and longitude.
    '''
    G = nx.Graph()

    for node_id, (lat, lon) in nodes.items():
        G.add_node(node_id, pos=(lon, lat))
    G.add_edges_from(edges)
    
    return G


def visualize_with_networkx(nodes: List[dict], edges: List[dict]) -> None:
    '''
    Visualizes a graph using NetworkX.

    Args:
        nodes (list): A list of node dictionaries, where each dictionary contains 
                      'id', 'latitude', 'longitude', and optionally 'name' attributes.
        edges (list): A list of edge dictionaries, where each dictionary contains 
                      'source', 'target', and 'weight' attributes.

    Returns:
        None
    '''
    G = nx.Graph()

    for node in nodes:
        G.add_node(node['id'], **node)
    for edge in edges:
        G.add_edge(edge['source'], edge['target'], weight=edge['weight'])

    pos = {node['id']: (node['longitude'], node['latitude']) for node in nodes}

    nx.draw_networkx_nodes(G, pos, node_size=300, node_color='skyblue')
    nx.draw_networkx_edges(G, pos, width=1.0, alpha=0.7)

    labels = {node['id']: node['name'] for node in nodes}
    nx.draw_networkx_labels(G, pos, labels, font_size=12)
 
    plt.title("Map Visualization using NetworkX")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.show()


def visualize_with_folium(nodes: List[dict], 
                          edges: List[dict], 
                          points_format="google") -> folium.Map:
    '''
    Visualizes a graph using folium. 
    Reads nodes / edges format according to argument points_format (google / overpass)

    Args:
        nodes (list): A list of node dictionaries, where each dictionary contains 
                      'id', 'latitude', 'longitude', and optionally 'name' attributes.
        edges (list): A list of edge dictionaries, where each dictionary contains 
                      'source', 'target', and 'weight' attributes.
        points_format (str): "google" | "overpass",  representing input format. 

    Returns:
        None
    '''

    if points_format == "google":

        avg_lat = sum(node['latitude'] for node in nodes) / len(nodes)
        avg_lon = sum(node['longitude'] for node in nodes) / len(nodes)

        m = folium.Map(location=[avg_lat, avg_lon], zoom_start=15)

        for node in nodes:
            folium.CircleMarker(
                location=[node['latitude'], node['longitude']],
                radius=5,
                popup=f"ID: {node['id']}<br>Name: {node['name']}",
                color='blue',
                fill=True,
                fill_color='skyblue'
            ).add_to(m)
        for edge in edges:
            source_node = next(node for node in nodes if node['id'] == edge['source'])
            target_node = next(node for node in nodes if node['id'] == edge['target'])
            folium.PolyLine(
                locations=[
                    [source_node['latitude'], source_node['longitude']],
                    [target_node['latitude'], target_node['longitude']]
                ],
                color='red',
                weight=2,
                opacity=0.8
            ).add_to(m)
        
    elif points_format == "overpass":

        avg_lat = sum(node['lat'] for node in nodes) / len(nodes)
        avg_lon = sum(node['lon'] for node in nodes) / len(nodes)

        m = folium.Map(location=[avg_lat, avg_lon], zoom_start=15)

        for node in nodes:
            folium.CircleMarker(
                location=[node['lat'], node['lon']],
                radius=4,
                popup=f"ID: {node['id']}<br>Tags: {node['tags'].__str__() if "tags" in node.keys() else ""}",
                color='blue',
                fill=True,
                fill_color='skyblue'
            ).add_to(m)
        for edge in edges:
            source_node = next(node for node in nodes if node['id'] == edge['source'])
            target_node = next(node for node in nodes if node['id'] == edge['target'])
            folium.PolyLine(
                locations=[
                    [source_node['lat'], source_node['lon']],
                    [target_node['lat'], target_node['lon']]
                ],
                color='red',
                weight=2,
                opacity=0.8
            ).add_to(m)
    
    else:
        raise ValueError("Bad input type for (points_format)")

    return m


def save_to_json(data, filename='nearest_roads.json'):
    with open(filename, 'w') as json_file:
        json.dump(data, json_file, indent=4)
    print(f"Data saved to {filename}")


if __name__ == "__main__":
    nodes = [
        {'id': 1, 'latitude': 37.7749, 'longitude': -122.4194},
        {'id': 2, 'latitude': 37.7750, 'longitude': -122.4180},
        {'id': 3, 'latitude': 37.7740, 'longitude': -122.4170},
        {'id': 4, 'latitude': 37.7730, 'longitude': -122.4185},
        {'id': 5, 'latitude': 37.7735, 'longitude': -122.4200}
    ]

    edges = [
        {'source': 1, 'target': 2},
        {'source': 2, 'target': 3},
        {'source': 3, 'target': 4},
        {'source': 4, 'target': 5},
        {'source': 5, 'target': 1},
        {'source': 2, 'target': 5}
    ]

    map_visualization = visualize_with_folium(nodes, edges)
    map_visualization.save('map.html')
