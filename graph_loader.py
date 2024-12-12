import sys
import os
import math
import heapq

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

def get_rel_direction(curr_coord: Tuple[float, float], 
                      target_coord: Tuple[float, float], 
                      heading: int) -> str:
    """
    Suppose there is a people at `coord1`, facing towards `heading` direction.
    Calculates relative location of coord2.
    Returns: Str["Same" | "Front" | "Right-Front" | "Right" | "Right-Back" | "Back" | "Left-Back" | "Left" | "Left-Front"]
    
    ----- This is latitude
    | | | This is longtitude

      ^ Define this direction as heading = 0
      |
      + --- > Define this direction as heading = 90
    
    Remark: Either heading in [-180, 180] or [0, 360] will work here.
    """
    
    lat1, lon1 = curr_coord
    lat2, lon2 = target_coord

    if abs(lat1 - lat2) < 1e-6 and abs(lon1 - lon2) < 1e-6:
        return "Same"

    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    bearing = math.atan2(x, y)
    bearing = (math.degrees(bearing) + 360) % 360

    relative_bearing = (bearing - heading + 360) % 360
    directions = ["Front", "Right-Front", "Right", "Right-Back", "Back", "Left-Back", "Left", "Left-Front"]
    direction_index = round(relative_bearing / 45) % 8
    
    return directions[direction_index]

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

        # used to mark graph edges
        self.min_lat = float("inf")
        self.max_lat = float("-inf")
        self.min_lng = float("inf")
        self.max_lng = float("-inf")
        
    def add_node(self, panoid, pano_yaw_angle, lat, lng):
        self.nodes[panoid] = Node(panoid, pano_yaw_angle, lat, lng)
        
        self.min_lat = min(self.min_lat, lat)
        self.max_lat = max(self.max_lat, lat)
        self.min_lng = min(self.min_lng, lng)
        self.max_lng = max(self.max_lng, lng)

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

    def get_abs_direction(self, coord: Tuple[float, float], 
                                mid_percentage = 0.2) -> str:
        """
        Suppose there is a person at `coord` (latitude, longitude).
        Calculates their relative position to the middle point of the graph.
        Returns a string indicating the relative position:
        "Middle", "North", "North-East", "East", "South-East", "South", "South-West", "West", "North-West".
        """
        mid_lat = (self.min_lat + self.max_lat) / 2
        mid_lng = (self.min_lng + self.max_lng) / 2
        R = mid_percentage * haversine((self.min_lat, self.min_lng), (self.max_lat, self.max_lng))

        lat, lng = coord

        if abs(lat - mid_lat) < R and abs(lng - mid_lng) < R:
            return "Middle"

        lat1, lon1 = math.radians(mid_lat), math.radians(mid_lng)
        lat2, lon2 = math.radians(lat), math.radians(lng)
        
        dlon = lon2 - lon1
        x = math.sin(dlon) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        
        bearing = math.atan2(x, y)
        bearing = math.degrees(bearing)
        if bearing < 0:
            bearing += 360

        if 337.5 <= bearing < 22.5:
            return "North"
        elif 22.5 <= bearing < 67.5:
            return "North-East"
        elif 67.5 <= bearing < 112.5:
            return "East"
        elif 112.5 <= bearing < 157.5:
            return "South-East"
        elif 157.5 <= bearing < 202.5:
            return "South"
        elif 202.5 <= bearing < 247.5:
            return "South-West"
        elif 247.5 <= bearing < 292.5:
            return "West"
        elif 292.5 <= bearing < 337.5:
            return "North-West"

class GraphLoader:
    def __init__(self, cfg: dict=None):
        self.graph = Graph()
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
    cfg = {
        "node": "output/overpass_streetmap/touchdown/nodes.txt",
        "link": "output/overpass_streetmap/touchdown/links.txt"
    }
    g = GraphLoader(cfg).construct_graph()
    #print(haversine((40.744981, -73.978682),(40.744904, -73.978949)))
    print(get_rel_direction(curr_coord=(0, 0), 
                            target_coord=(10, 0), 
                            heading=-90))
