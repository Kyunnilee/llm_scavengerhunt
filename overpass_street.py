# -*- coding:utf-8 -*-

from typing import *
import requests
import networkx as nx
import matplotlib.pyplot as plt
import json
import util

# NOTE: you DON'T need a overpass API_KEY.
overpass_url = "http://overpass-api.de/api/interpreter"


def get_roads_in_area(bbox: Tuple[float, float, float, float], 
                      force_use_local_path: str = "", 
                      save_to_local_path: str = "") -> Tuple[dict, dict]:
    """
    Return (nodes, edges) in a designated area.

    Args: 
        bbox: (latitude_min, longitude_min, latitude_max, longitude_max)
            This is equivilant to: (south, west, north, east)
        force_use_local_path: use local data instead of querying server.
        save_to_local_path: save raw data json to local path (if server is quried)

    Returns:
        nodes
        edges
    """

    if not force_use_local_path:
        # query server api
        overpass_query = f"""
            [out:json];
            (
            way["highway"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
            >;
            );
            out body;
        """
        response = requests.get(overpass_url, params={'data': overpass_query})
        data = response.json()

        # save to local json
        if save_to_local_path:
            with open(save_to_local_path, "w") as fileobj:
                json.dump(data, fileobj)
    
    else:
        with open(force_use_local_path, "r") as fileobj:
            data = json.load(fileobj)

    nodes = []
    edges = []

    for element in data['elements']:
        if element['type'] == 'node':
            nodes.append(element)
        elif element['type'] == 'way':
            way_nodes = element['nodes']
            for i in range(len(way_nodes) - 1):
                edges.append(
                    {"source": way_nodes[i], "target": way_nodes[i + 1]}
                )

    return nodes, edges


if __name__ == "__main__":
    # (latitude_min, longitude_min, latitude_max, longitude_max)
    bbox = [37.7749, -122.4194, 37.7849, -122.4094]

    nodes, edges = get_roads_in_area(
        bbox, force_use_local_path="output/overpass_streetmap/raw_query_result.json"
    )
    print(nodes)
    map_object = util.visualize_with_folium(nodes, edges, points_format="overpass")
    map_object.save("./output/overpass_streetmap/map.html")
