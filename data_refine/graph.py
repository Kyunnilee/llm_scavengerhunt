import sys
import os
import math
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

class Node:
    def __init__(self, panoid, pano_yaw_angle, lat, lng):
        self.panoid = panoid
        self.pano_yaw_angle = pano_yaw_angle
        self.neighbors = {}
        self.coordinate = (lat, lng)


class Graph:
    def __init__(self):
        self.nodes = {}
        
    def _add_node(self, panoid, pano_yaw_angle, lat, lng):
        self.nodes[panoid] = Node(panoid, pano_yaw_angle, lat, lng)

    def _add_edge(self, start_panoid, end_panoid, heading):
        start_node = self.nodes[start_panoid]
        end_node = self.nodes[end_panoid]
        heading = math.atan2(
            end_node.coordinate[1] - start_node.coordinate[1], 
            end_node.coordinate[0] - start_node.coordinate[0]
        ) / math.pi * 180
        start_node.neighbors[heading] = end_node
        
    def add_node(self, panoid, lat, lng):
        if panoid in self.nodes:
            raise ValueError(f'Node {panoid} already exists.')
        self._add_node(panoid, 0, lat, lng)
        
    def add_edge(self, start_panoid, end_panoid):
        if (start_panoid not in self.nodes) or (end_panoid not in self.nodes):
            raise ValueError(f'Node not found.')
        start_node_pos = self.nodes[start_panoid].coordinate
        end_node = self.nodes[end_panoid].coordinate
        heading = math.atan2(end_node[1] - start_node_pos[1], end_node[0] - start_node_pos[0]) / math.pi * 180
        heading = int(heading)
        self._add_edge(start_panoid, end_panoid, heading)
        
    def del_edge(self, start_panoid, end_panoid):
        start_node = self.nodes[start_panoid]
        for node_id, node in start_node.neighbors.items():
            if node.panoid == end_panoid:
                del start_node.neighbors[node_id]
                return
        raise ValueError(f'Edge {start_panoid} -> {end_panoid} not found.')
    
    def del_node(self, panoid):
        del_node:Node = self.nodes[panoid]
        del_edge_list = []
        for node_id in self.nodes:
            if node_id is del_node.panoid: continue
            for heading, end_node in self.nodes[node_id].neighbors.items():
                if end_node is del_node:
                    del_edge_list.append((node_id, heading))
        
        for start_panoid, heading in del_edge_list:
            self.del_edge(start_panoid, panoid)
            
        del self.nodes[panoid]
        
    def get_vis_data(self,chosen_nodes=[],chosen_edges=[]):
        nodes_vis = []
        edges_vis = []
        for node_id in self.nodes:
            nodes_vis.append({
                'id': node_id,
                'name': node_id,
                'latitude': self.nodes[node_id].coordinate[0],
                'longitude': self.nodes[node_id].coordinate[1],
                'chosen': True if node_id in chosen_nodes else False
            })
            for heading, end_node in self.nodes[node_id].neighbors.items():
                edges_vis.append({
                    'source': node_id,
                    'target': end_node.panoid,
                    'weight': 1,
                    'chosen': True if (node_id, end_node.panoid) in chosen_edges else False
                })
        return nodes_vis, edges_vis
    
    def get_txt_file(self, save_root):
        node_file = os.path.join(save_root, 'nodes.txt')
        link_file = os.path.join(save_root, 'links.txt')
        
        node_added = set()
        edge_added = set()
        with open(node_file, 'w') as f:
            for node_id in self.nodes:
                node:Node = self.nodes[node_id]
                if node.neighbors == {}:
                    print(f'Node {node_id} has no neighbors.')
                if node_id not in node_added:
                    f.write(f'{node_id},{node.pano_yaw_angle},{node.coordinate[0]},{node.coordinate[1]}\n')
                    node_added.add(node_id)
                    
        with open(link_file, 'w') as f:
            for node_id in self.nodes:
                for heading, end_node in self.nodes[node_id].neighbors.items():
                    edge = tuple(sorted(node_id, end_node.panoid))
                    if edge not in edge_added:  
                        f.write(f'{node_id},{heading},{end_node.panoid}\n')
                        edge_added.add(edge)
                    else:
                        print(f'Edge {edge} already added.')
                    
        print(f'Nodes file saved to {node_file}')
        print(f'Links file saved to {link_file}')
        
class GraphLoader:
    def __init__(self, cfg: dict):
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
                self.graph._add_node(panoid, int(pano_yaw_angle), float(lat), float(lng))

        with open(self.link_file) as f:
            for line in f:
                start_panoid, heading, end_panoid = line.strip().split(',')
                self.graph._add_edge(start_panoid, end_panoid, int(heading))

        num_edges = 0
        for panoid in self.graph.nodes.keys():
            num_edges += len(self.graph.nodes[panoid].neighbors)

        print('===== Graph loaded =====')
        print('Number of nodes:', len(self.graph.nodes))
        print('Number of edges:', num_edges)
        print('========================')
        return self.graph
    
if __name__ == "__main__":
    import random
    from util import visualize_with_folium_with_choose
    config = {'node': r'..\output\overpass_streetmap\touchdown\nodes.txt',
              'link': r'..\output\overpass_streetmap\touchdown\links.txt'}
    graph = GraphLoader(config).construct_graph()
    chosen_nodes = random.sample(list(graph.nodes.keys()), 5)
    print(chosen_nodes)
    nodes_vis, edges_vis = graph.get_vis_data(chosen_nodes=chosen_nodes)
    # print(nodes_vis)
    # print(edges_vis)
    v = visualize_with_folium_with_choose(nodes_vis, edges_vis)
    v.save(r'./tmp.html')
    # graph.get_txt_file(r"tmp")

