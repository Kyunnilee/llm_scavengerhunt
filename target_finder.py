import googlemaps
import json
import os
from collections import deque
from typing import List, Set, Dict, Tuple
import math

# Configuration parameters
INITIAL_LATITUDE = 37.7805979
INITIAL_LONGITUDE = -122.417003
SEARCH_RADIUS = 1000  # in meters
LANDMARK_KEYWORDS = ["landmark", "shopping mall", "tourist attraction"]
NUM_TARGET_NODES = 1  # number of closest nodes to target to be considered as endpoints
GOOGLE_API_KEY = "AIzaSyC04gYkv5OP4fqaKx6etfcdd6oPGELNmi8"
NODE_FILE = r'output/overpass_streetmap/touchdown/nodes.txt'
LINK_FILE = r'output/overpass_streetmap/touchdown/links.txt'
OUTPUT_FILE = "output/possible_starts.json"

class Node:
    def __init__(self, panoid: str, pano_yaw_angle: int, lat: float, lng: float):
        """A node in the street view graph with location and connectivity information."""
        self.panoid = panoid
        self.pano_yaw_angle = pano_yaw_angle
        self.neighbors = {}  # {heading: neighbor_node}
        self.coordinate = (lat, lng)

class Graph:
    def __init__(self):
        """A graph structure for street view navigation."""
        self.nodes = {}
        
    def add_node(self, panoid: str, pano_yaw_angle: int, lat: float, lng: float):
        """Add a new node with its panorama and location data."""
        self.nodes[panoid] = Node(panoid, pano_yaw_angle, lat, lng)

    def add_edge(self, start_panoid: str, end_panoid: str, heading: int):
        """Add a directed edge with calculated heading based on coordinates."""
        start_node = self.nodes[start_panoid]
        end_node = self.nodes[end_panoid]
        heading = math.atan2(
            end_node.coordinate[1] - start_node.coordinate[1], 
            end_node.coordinate[0] - start_node.coordinate[0]
        ) / math.pi * 180
        start_node.neighbors[heading] = end_node

class GraphLoader:
    def __init__(self, node_file: str = NODE_FILE, link_file: str = LINK_FILE):
        """Initialize graph loader with file paths for nodes and edges."""
        self.graph = Graph()
        self.node_file = node_file
        self.link_file = link_file
        print('Loading graph...')
        print('Node file:', self.node_file)
        print('Link file:', self.link_file)

    def construct_graph(self) -> Graph:
        """Build the graph from node and link files, creating bidirectional edges."""
        # Load nodes
        with open(self.node_file) as f:
            for line in f:
                panoid, pano_yaw_angle, lat, lng = line.strip().split(',')
                pano_yaw_angle = 0  # Reset all angles to 0
                self.graph.add_node(panoid, int(pano_yaw_angle), float(lat), float(lng))

        # Load edges
        with open(self.link_file) as f:
            for line in f:
                start_panoid, heading, end_panoid = line.strip().split(',')
                self.graph.add_edge(start_panoid, end_panoid, int(heading))
                # Add reverse edge with opposite heading
                self.graph.add_edge(end_panoid, start_panoid, (int(heading) + 180) % 360)

        # Print graph statistics
        num_edges = sum(len(node.neighbors) for node in self.graph.nodes.values())
        print('===== Graph loaded =====')
        print('Number of nodes:', len(self.graph.nodes))
        print('Number of edges:', num_edges)
        print('========================')
        return self.graph

def find_landmarks(api_key: str, latitude: float, longitude: float, radius: int, 
                  keywords: List[str]) -> List[Dict]:
    """
    Find landmarks near the location with detailed descriptions from Google Places API.
    Includes place details and reviews for comprehensive location information.
    """
    gmaps = googlemaps.Client(key=api_key)
    results = []

    places = gmaps.places_nearby(
        location=(latitude, longitude), 
        radius=radius, 
        keyword="|".join(keywords)
    )

    for place in places.get('results', []):
        # Get detailed place information including reviews
        place_details = gmaps.place(place['place_id'], fields=['reviews'])
        
        name = place.get('name')
        location = place.get('geometry', {}).get('location', {})
        lat, lng = location.get('lat'), location.get('lng')
        address = place.get('vicinity', 'Unknown location')
        
        # Extract descriptions from reviews
        reviews = place_details.get('result', {}).get('reviews', [])
        descriptions = [review['text'] for review in reviews[:3] if review.get('text')]
        feature_description = '. '.join(descriptions) if descriptions else "No detailed description available."
        
        results.append({
            "name": name,
            "latitude": lat,
            "longitude": lng,
            "address": address,
            "description": f"{name} is located at {address}",
            "feature_description": feature_description
        })

    return results

def find_closest_nodes(graph: Graph, target_lat: float, target_lng: float, 
                      num_nodes: int) -> List[str]:
    """Find the closest nodes to target location using Euclidean distance."""
    distances = []
    for node_id, node in graph.nodes.items():
        lat, lng = node.coordinate
        dist = ((lat - target_lat) ** 2 + (lng - target_lng) ** 2) ** 0.5
        distances.append((dist, node_id))
    
    distances.sort()
    return [node_id for _, node_id in distances[:num_nodes]]

def find_nodes_within_steps(graph: Graph, end_nodes: List[str], max_steps: int) -> Set[str]:
    """
    Helper function that finds all nodes that can reach end nodes within specified maximum steps.
    """
    visited = set()
    result_nodes = set()
    queue = deque()
    
    # Build reverse adjacency map
    reverse_adj = {node_id: set() for node_id in graph.nodes}
    for node_id, node in graph.nodes.items():
        for heading, neighbor in node.neighbors.items():
            reverse_adj[neighbor.panoid].add(node_id)
    
    # Start BFS from end nodes
    for end_node in end_nodes:
        queue.append((end_node, 0))
        visited.add((end_node, 0))
        result_nodes.add(end_node)
    
    while queue:
        current_node, steps = queue.popleft()
        
        if steps >= max_steps:
            continue
            
        for prev_node_id in reverse_adj[current_node]:
            next_steps = steps + 1
            visit_key = (prev_node_id, next_steps)
            
            if visit_key not in visited:
                visited.add(visit_key)
                queue.append((prev_node_id, next_steps))
                result_nodes.add(prev_node_id)
    
    return result_nodes

def find_possible_start_nodes(graph: Graph, end_nodes: List[str], 
                            min_steps: int, max_steps: int) -> Set[str]:
    """
    Find all nodes that can reach the target nodes within the specified step range.
    Uses set difference between two BFS results to get nodes in the desired range.
    """
    # Find all nodes reachable within max_steps
    nodes_within_max = find_nodes_within_steps(graph, end_nodes, max_steps)
    
    # Find all nodes reachable within (min_steps - 1)
    nodes_within_min_minus_one = find_nodes_within_steps(graph, end_nodes, min_steps - 1)
    
    # The difference gives us nodes that are exactly within our desired range
    return nodes_within_max - nodes_within_min_minus_one
def format_start_points(graph: Graph, node_ids: Set[str]) -> List[Dict]:
    """Format node data for output with location information."""
    return [{
        "node_id": node_id,
        "latitude": graph.nodes[node_id].coordinate[0],
        "longitude": graph.nodes[node_id].coordinate[1]
    } for node_id in node_ids]

def main():
    # Load the street view graph
    graph_loader = GraphLoader()
    street_graph = graph_loader.construct_graph()
    
    # Find nearby landmarks with detailed information
    locations = find_landmarks(
        GOOGLE_API_KEY, 
        INITIAL_LATITUDE, 
        INITIAL_LONGITUDE, 
        SEARCH_RADIUS, 
        LANDMARK_KEYWORDS
    )

    # Display available locations
    print("\nAvailable landmarks:")
    for i, loc in enumerate(locations):
        print(f"{i}: {loc['name']} ({loc['latitude']}, {loc['longitude']}) - {loc['description']}")

    # Get user selection
    selected_index = int(input("\nEnter the number of the target location: "))
    target_location = locations[selected_index]
    print(f"Selected target: {target_location['name']}")

    # Find closest nodes to target
    target_nodes = find_closest_nodes(
        street_graph,
        target_location["latitude"],
        target_location["longitude"],
        NUM_TARGET_NODES
    )
    print(f"\nTarget nodes: {target_nodes}")

    # Get step range from user
    min_steps = int(input("Enter the minimum number of steps: "))
    max_steps = int(input("Enter the maximum number of steps: "))

    # Find possible start nodes
    possible_starts = find_possible_start_nodes(
        street_graph, 
        target_nodes, 
        min_steps, 
        max_steps
    )

    # Format results with enhanced information
    start_points = format_start_points(street_graph, possible_starts)
    
    # Prepare target nodes information
    target_nodes_info = [{
        "node_id": node_id,
        "latitude": street_graph.nodes[node_id].coordinate[0],
        "longitude": street_graph.nodes[node_id].coordinate[1]
    } for node_id in target_nodes]
    
    # Prepare complete output data
    output_data = {
        "target_location": {
            "name": target_location["name"],
            "latitude": target_location["latitude"],
            "longitude": target_location["longitude"],
            "address": target_location["address"],
            "description": target_location["description"],
            "feature_description": target_location["feature_description"]
        },
        "target_nodes": target_nodes_info,
        "start_points": start_points
    }

    print(f"\nFound {len(start_points)} possible start points")

    with open(OUTPUT_FILE, "w") as f:
        json.dump(output_data, f, indent=4)
    print(f"Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()