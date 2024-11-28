# -*- coding:utf-8 -*-

import folium
import networkx as nx
import matplotlib.pyplot as plt
import json
import pandas as pd
import os
from typing import *
from tqdm import tqdm
import requests
import math


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
                popup=f"ID: {node['id']}<br>Tags: {node['tags'].__str__() if 'tags' in node.keys() else ''}",
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

def visualize_with_folium_with_choose(nodes: List[dict], 
                          edges: List[dict], 
                          points_format="google") -> folium.Map:
    '''
    Visualizes a graph using folium. 
    Reads nodes / edges format according to argument points_format (google / overpass)
    Chosen nodes and edges are highlighted.

    Args:
        nodes (list): A list of node dictionaries, where each dictionary contains 
                      'id', 'latitude', 'longitude', 'chosen', and optionally 'name' attributes.
        edges (list): A list of edge dictionaries, where each dictionary contains 
                      'source', 'target', 'weight' and 'chosen' attributes.
        points_format (str): "google" | "overpass",  representing input format. 

    Returns:
        None
    '''

    if points_format == "google":

        avg_lat = sum(node['latitude'] for node in nodes) / len(nodes)
        avg_lon = sum(node['longitude'] for node in nodes) / len(nodes)

        m = folium.Map(location=[avg_lat, avg_lon], zoom_start=15)

        for node in nodes:
            if node['chosen']:
                color = 'red'
            else:
                color = 'blue'
            folium.CircleMarker(
                location=[node['latitude'], node['longitude']],
                radius=5,
                popup=f"ID: {node['id']}<br>Name: {node['name']}",
                color=color,
                fill=True,
                fill_color=color
            ).add_to(m)
        for edge in edges:
            source_node = next(node for node in nodes if node['id'] == edge['source'])
            target_node = next(node for node in nodes if node['id'] == edge['target'])
            if edge['chosen']:
                color = 'red'
            else:
                color = 'black'
            folium.PolyLine(
                locations=[
                    [source_node['latitude'], source_node['longitude']],
                    [target_node['latitude'], target_node['longitude']]
                ],
                color=color,
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
                popup=f"ID: {node['id']}<br>Tags: {node['tags'].__str__() if 'tags' in node.keys() else ''}",
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


def visualize_touchdown(folder_path, output_html="network_map.html"):
    nodes_file = folder_path + "/" + "nodes.txt"
    links_file = folder_path + "/" + "links.txt"
    
    nodes_df = pd.read_csv(nodes_file, header=None, names=["id", "unused", "lat", "lon"])
    nodes_df.drop(columns=["unused"], inplace=True)

    links_df = pd.read_csv(links_file, header=None, names=["id1", "unused", "id2"])
    links_df.drop(columns=["unused"], inplace=True)

    if not nodes_df.empty:
        map_center = [nodes_df["lat"].mean(), nodes_df["lon"].mean()]
    else:
        map_center = [0, 0]

    folium_map = folium.Map(location=map_center, zoom_start=12)

    nodes_dict = {}
    for _, row in tqdm(nodes_df.iterrows()):
        node_id = row["id"]
        lat, lon = row["lat"], row["lon"]
        nodes_dict[node_id] = (lat, lon)

        folium.CircleMarker(
            location=[lat, lon],
            radius=4,
            popup=f"Node ID: {node_id}",
            color='blue',
            fill=True,
            fill_color='skyblue'
        ).add_to(folium_map)

        # folium.Marker(
        #     location=[lat, lon],
        #     popup=f"Node ID: {node_id}",
        #     icon=folium.Icon(color="blue", icon="info-sign")
        # ).add_to(folium_map)

    for _, row in tqdm(links_df.iterrows()):
        id1, id2 = row["id1"], row["id2"]

        if id1 in nodes_dict and id2 in nodes_dict:
            lat_lon1 = nodes_dict[id1]
            lat_lon2 = nodes_dict[id2]

            folium.PolyLine(
                locations=[lat_lon1, lat_lon2],
                color="red",
                weight=2
            ).add_to(folium_map)

    folium_map.save(output_html)
    print(f"saved to {output_html}")
        
# class AgentVisualization0():
#     def __init__(self, graph, vis_root):
#         self.vis_root = vis_root
#         self.nx_graph = nx.Graph()
#         self.nodes = {} # panoid: (lat, lon)
#         self.current_node = None
#         self.visited_nodes = set()
#         self.candidate_nodes = None
        
#         # get min and max lat, lon
#         min_lat, min_lon, max_lat, max_lon = 90, 180, -90, -180
#         for nodeid, node in graph.nodes.items():
#             min_lat = min(min_lat, node.coordinate[0])
#             min_lon = min(min_lon, node.coordinate[1])
#             max_lat = max(max_lat, node.coordinate[0])
#             max_lon = max(max_lon, node.coordinate[1])
    
#         # add nodes and edges
#         for nodeid, node in graph.nodes.items():
#             y_pixel, x_pixel = node.coordinate  
#             self.nodes[node.panoid] = (x_pixel, y_pixel)
#         self.nx_graph.add_nodes_from(self.nodes.keys())
        
#         for nodeid, node in graph.nodes.items():
#             for heading, end_node in node.neighbors.items():
#                 self.nx_graph.add_edge(node.panoid, end_node.panoid)
        
#         # set up matplotlib
#         plt.ion()
#         fig, self.ax = plt.subplots(figsize=(10, 10))
#         self.ax.set_xlim(min_lon, max_lon)
#         self.ax.set_ylim(min_lat, max_lat)
    
#     def update_plot(self, new_node, candidate_nodes=None):
#         if self.current_node:
#             self.visited_nodes.add(self.current_node)
#         self.current_node = new_node
#         self.candidate_nodes = candidate_nodes
        
#         self.ax.clear()
#         colors = []
#         for node in self.nx_graph.nodes:
#             if self.current_node and node == self.current_node:
#                 colors.append('red')
#             elif self.candidate_nodes and node == self.candidate_nodes:
#                 colors.append('green')
#             elif node in self.visited_nodes:
#                 colors.append('gray')
#             else:
#                 colors.append('blue')
#         nx.draw_networkx_nodes(self.nx_graph, pos=self.nodes, ax=self.ax, node_color=colors, node_size=1)
#         nx.draw_networkx_edges(self.nx_graph, pos=self.nodes, ax=self.ax, width=1.0, alpha=0.7)
#         # nx.draw_networkx_labels(self.nx_graph, pos=self.nodes, ax=self.ax)
#         plt.draw()
#         plt.pause(0.1)
        
class AgentVisualization():
    def __init__(self,graph, vis_root, zoom=19):
        self.vis_root = os.path.join(vis_root, "agent_vis")
        os.makedirs(self.vis_root, exist_ok=True)
        
        self.nodes = {} # panoid: (lat, lon)
        self.current_node = None
        self.visited_nodes = []
        self.candidate_nodes = []
        self.nodes = {node.panoid: node.coordinate for node in graph.nodes.values()}
        
        # para for api
        self.zoom = zoom
        self.limit_distance = 0.001
        
        # set up matplotlib
        plt.ion()
        fig, self.ax = plt.subplots(figsize=(10, 10))
        
        self.step = 0

    def get_google_map_image(self):
        base_url = "https://maps.googleapis.com/maps/api/staticmap"
        
        current_node_pos = self.nodes[self.current_node]
        current_marker = f"&markers=size:mid|color:red|{current_node_pos[0]}, {current_node_pos[1]}"
        
        candidate_markers = f"&markers=size:mid|color:green"
        for node in self.candidate_nodes:
            node_pos = self.nodes[node]
            candidate_markers += f"|{node_pos[0]}, {node_pos[1]}"
        candidate_markers = candidate_markers[:-1]
        
        other_markers = f"&markers=size:tiny|color:blue"
        for node_id, node_pos in self.nodes.items():
            distance = math.sqrt((node_pos[0] - current_node_pos[0])**2 + (node_pos[1] - current_node_pos[1])**2)
            if distance > self.limit_distance: continue
            
            if node_id != self.current_node and node_id not in self.candidate_nodes:
                other_markers += f"|{node_pos[0]}, {node_pos[1]}"
        
        visited_path = f"&path=color:0x0000ff|weight:5"
        for node in self.visited_nodes:
            node_pos = self.nodes[node]
            visited_path += f"|{node_pos[0]}, {node_pos[1]}"
        visited_path += f"|{current_node_pos[0]}, {current_node_pos[1]}"
            
        full_url = f"{base_url}?center={current_node_pos[0]}, {current_node_pos[1]}&zoom={self.zoom}&size=640x640&maptype=roadmap{current_marker}{candidate_markers}{other_markers}{visited_path}&key={os.environ.get('GOOGLE_API_KEY')}"

        response = requests.get(full_url)
        
        filename = os.path.join(self.vis_root, f"step_{self.step}.png")
        if response.status_code == 200:
            with open(filename, 'wb') as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            print(f"Map with markers saved as {filename}")
            return filename
        else:
            return f"Error: Unable to retrieve map (Status code: {response.status_code})"
    
    def update(self, new_node, candidate_nodes):
        self.visited_nodes.append(self.current_node)
        self.current_node = new_node
        self.candidate_nodes = candidate_nodes
        self.step += 1
        self.ax.clear()
        img = plt.imread(self.get_google_map_image())
        self.ax.imshow(img)
        plt.draw()
        plt.pause(0.1)
        
    def init_current_node(self, node):
        self.current_node = node


if __name__ == "__main__":
    visualize_touchdown("../touchdown/graph", 
                        "touchdown_map.html")
    # nodes = [
    #     {'id': 1, 'latitude': 37.7749, 'longitude': -122.4194},
    #     {'id': 2, 'latitude': 37.7750, 'longitude': -122.4180},
    #     {'id': 3, 'latitude': 37.7740, 'longitude': -122.4170},
    #     {'id': 4, 'latitude': 37.7730, 'longitude': -122.4185},
    #     {'id': 5, 'latitude': 37.7735, 'longitude': -122.4200}
    # ]

    # edges = [
    #     {'source': 1, 'target': 2},
    #     {'source': 2, 'target': 3},
    #     {'source': 3, 'target': 4},
    #     {'source': 4, 'target': 5},
    #     {'source': 5, 'target': 1},
    #     {'source': 2, 'target': 5}
    # ]

    # map_visualization = visualize_with_folium(nodes, edges)
    # map_visualization.save('map.html')
