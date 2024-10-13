# -*- coding:utf-8 -*-

import util

nodes = [
    {'id': 1, 'name': 'A', 'latitude': 37.7749, 'longitude': -122.4194},
    {'id': 2, 'name': 'B', 'latitude': 37.7750, 'longitude': -122.4180},
    {'id': 3, 'name': 'C', 'latitude': 37.7740, 'longitude': -122.4170},
    {'id': 4, 'name': 'D', 'latitude': 37.7730, 'longitude': -122.4185},
    {'id': 5, 'name': 'E', 'latitude': 37.7735, 'longitude': -122.4200}
]

edges = [
    {'source': 1, 'target': 2, 'weight': 1.0},
    {'source': 2, 'target': 3, 'weight': 1.2},
    {'source': 3, 'target': 4, 'weight': 0.9},
    {'source': 4, 'target': 5, 'weight': 1.1},
    {'source': 5, 'target': 1, 'weight': 1.3},
    {'source': 2, 'target': 5, 'weight': 0.8}
]


# visualize_with_networkx(nodes, edges)
map_visualization = util.visualize_with_folium(nodes, edges)
map_visualization.save('map.html')
