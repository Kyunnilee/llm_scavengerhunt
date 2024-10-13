# -*- coding:utf-8 -*-

import folium
import networkx as nx
import matplotlib.pyplot as plt
import json


def visualize_with_networkx(nodes, edges):
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


def visualize_with_folium(nodes, edges):
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

    return m

def save_to_json(data, filename='nearest_roads.json'):
    with open(filename, 'w') as json_file:
        json.dump(data, json_file, indent=4)
    print(f"Data saved to {filename}")