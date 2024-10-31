import sys
import os
import gradio as gr
import tempfile
import base64
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from data_refine.graph import *
from util import visualize_with_folium_with_choose

class GradioApp():
    def __init__(self, config:dict):
        
        self.graph = GraphLoader(config).construct_graph()
        
        
    def get_node(self):
        return list(self.graph.nodes.keys())
    
    def get_edge(self): 
        edge_list = []
        for node_id in self.graph.nodes:
            for heading, end_node in self.graph.nodes[node_id].neighbors.items():
                edge = (node_id, end_node.panoid)
                
                edge_list.append(str(edge)) # gradio not accept tuple
        return edge_list
    
    def edge_str_to_tuple(self, edge_str_list):
        return [eval(edge_str) for edge_str in edge_str_list]
    
    def display_graph(self, selected_nodes=[], selected_edges=[]):
        selected_edges_tuple = self.edge_str_to_tuple(selected_edges)
        node_vis, edge_vis = self.graph.get_vis_data(selected_nodes, selected_edges_tuple)
        vis = visualize_with_folium_with_choose(node_vis, edge_vis)
        temp_html_path = tempfile.NamedTemporaryFile(delete=False, suffix=".html").name
        vis.save(temp_html_path)
        print(f'Visualization saved to {temp_html_path}')
        
        with open(temp_html_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
        data_uri = "data:text/html;base64," + base64.b64encode(html_content.encode()).decode()
        
        return f'<iframe src="{data_uri}" width="100%" height="500px"></iframe>'
    
    def add_node(self, node_id, lat, lng):
        self.graph.add_node(node_id, lat, lng)
        return self.update()
        
    def add_edge(self, start_node_id, end_node_id):
        self.graph.add_edge(start_node_id, end_node_id)
        return self.update()
        
        
    def delete(self, nodes, edges):
        edges_tuple = self.edge_str_to_tuple(edges)
        for start_node_id, end_node_id in edges_tuple:
            self._delete_edge(start_node_id, end_node_id)
        for node_id in nodes:
            self._delete_node(node_id)
        return self.update()
        
    def _delete_node(self, node_id):
        self.graph.del_node(node_id)
        
    def _delete_edge(self, start_node_id, end_node_id):
        self.graph.del_edge(start_node_id, end_node_id)
        
        
    def update(self):
        nodes = self.get_node()
        edges = self.get_edge()
        return gr.update(value=[],choices=nodes), gr.update(value=[],choices=edges), gr.update(value=[],choices=nodes), gr.update(value=[],choices=nodes)
    
    