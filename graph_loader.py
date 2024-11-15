import sys
import os
import config.map_config as config
import math


class Node:
    def __init__(self, panoid, pano_yaw_angle, lat, lng):
        self.panoid = panoid
        self.pano_yaw_angle = pano_yaw_angle
        self.neighbors = {}
        self.coordinate = (lat, lng)


class Graph:
    def __init__(self):
        self.nodes = {}
        
    def add_node(self, panoid, pano_yaw_angle, lat, lng):
        self.nodes[panoid] = Node(panoid, pano_yaw_angle, lat, lng)

    def add_edge(self, start_panoid, end_panoid, heading):
        start_node = self.nodes[start_panoid]
        end_node = self.nodes[end_panoid]
        heading = math.atan2(
            end_node.coordinate[1] - start_node.coordinate[1], 
            end_node.coordinate[0] - start_node.coordinate[0]
        ) / math.pi * 180
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


class GraphLoader:
    def __init__(self, cfg: dict=None):
        self.graph = Graph()
        if cfg is None:
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

