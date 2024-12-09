import sys
import os
import math
import heapq
import config.map_config as config

from typing import *
from collections import deque

def haversine(coord1, coord2):
    """
    Calculate the Haversine distance between two coordinates (lat, lng).
    coord1, coord2: Tuples (latitude, longitude) in degrees.
    Returns: Distance in meters.
    """
    R = 6371000  # Earth radius in meters
    lat1, lon1 = map(math.radians, coord1)
    lat2, lon2 = map(math.radians, coord2)
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

class Node:
    def __init__(self, panoid, pano_yaw_angle, lat, lng):
        self.panoid: str = panoid
        self.pano_yaw_angle: int = pano_yaw_angle
        # for each node, neighbors: heading -> Node; heading in [-180, 180]
        self.neighbors: Dict[int, Node] = {}
        self.coordinate: Tuple[float, float] = (lat, lng)
    
    def __str__(self):
        neighbor_panoids = [node.panoid for node in self.neighbors.values()]
        return f"\"Node Object with panoid={self.panoid}, " \
                f"(lat, lng)=({self.coordinate[0]}, {self.coordinate[1]}), " \
                f"neighbours=({neighbor_panoids}), " \
                f"pano_yaw_angle={self.pano_yaw_angle}\"\n"
    
    def __repr__(self):
        return self.__str__()


class Graph:
    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        
    def add_node(self, panoid, pano_yaw_angle, lat, lng):
        self.nodes[panoid] = Node(panoid, pano_yaw_angle, lat, lng)

    def add_edge(self, start_panoid, end_panoid, heading):
        start_node = self.nodes[start_panoid]
        end_node = self.nodes[end_panoid]
        heading = math.atan2(
            end_node.coordinate[1] - start_node.coordinate[1], 
            end_node.coordinate[0] - start_node.coordinate[0]
        ) / math.pi * 180
        heading = int(heading)
        # if not start_node.neighbors[heading]:
        start_node.neighbors[heading] = end_node
        # else:
        #     raise ValueError(f'Edge {start_panoid} -> {end_panoid} already exists.')
        
    def get_node_coordinates(self, node_id):
        return self.nodes[node_id].coordinate
    
    def get_candidate_nodes(self, node_id, heading): # only return the node that has the same heading
        # candidate_nodes = []
        for heading2neighbor, neighbor in self.nodes[node_id].neighbors.items():
            # candidate_nodes.append(neighbor)
            if heading == heading2neighbor:
                return [neighbor]
        # return candidate_nodes
        return []

    def get_path(self, node_from, node_to):
        """
        Use BFS to find the shortest path (in terms of number of steps) 
        from node_from to node_to. 
        Returns a list of `panoid`s, indicating the path.
        """
        if node_from not in self.nodes or node_to not in self.nodes:
            raise ValueError("Both start and end nodes must exist in the graph.")
        
        # Queue for BFS
        queue = deque([(self.nodes[node_from], [])])  # (current_node, path_so_far)
        visited = set()
        
        while queue:
            current_node, path = queue.popleft()
            
            if current_node.panoid == node_to:
                return path + [current_node.panoid]
            
            if current_node.panoid in visited:
                continue
            visited.add(current_node.panoid)
            
            for neighbor_heading, neighbor in current_node.neighbors.items():
                if neighbor.panoid not in visited:
                    queue.append((neighbor, path + [current_node.panoid]))
        
        return None

class GraphLoader:
    def __init__(self, cfg: dict=None):
        self.graph = Graph()
        if cfg is None:
            print("Using Legacy Map Config...")
            self.node_file = config.paths['node']
            self.link_file = config.paths['link']
        else:
            self.node_file = cfg['node']
            self.link_file = cfg['link']
        print('Loading graph...')
        print('Node file:', self.node_file)
        print('Link file:', self.link_file)

    def construct_graph(self):
        with open(self.node_file) as f:
            for line in f:
                panoid, pano_yaw_angle, lat, lng = line.strip().split(',')
                
                pano_yaw_angle = 0 # set all pano_yaw_angle to 0. The heading of node will be determined at runtime.
                self.graph.add_node(panoid, int(pano_yaw_angle), float(lat), float(lng))

        with open(self.link_file) as f:
            for line in f:
                start_panoid, heading, end_panoid = line.strip().split(',')
                self.graph.add_edge(start_panoid, end_panoid, int(heading))
                self.graph.add_edge(end_panoid, start_panoid, (int(heading) + 180) % 360)

        num_edges = 0
        for panoid in self.graph.nodes.keys():
            num_edges += len(self.graph.nodes[panoid].neighbors)

        print('===== Graph loaded =====')
        print('Number of nodes:', len(self.graph.nodes))
        print('Number of edges:', num_edges)
        print('========================')
        return self.graph

if __name__ == "__main__":
    g = GraphLoader().construct_graph()
    # print(g.nodes)
    # path = g.get_path("1243846572", "6910182916")
    # print(path) 
