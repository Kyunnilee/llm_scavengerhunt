import gradio as gr
import networkx as nx
import matplotlib.pyplot as plt
from app_backend import GradioApp
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

config = {'node': os.path.join('touchdown', 'graph', 'our_graph', 'nodes.txt'),'link': os.path.join('touchdown', 'graph', 'our_graph', 'links.txt')}
gradio_app = GradioApp(config)

node_selection = gr.Dropdown(label="Choose Nodes", choices=gradio_app.get_node(), multiselect=True, filterable=True)
edge_selection = gr.Dropdown(label="Choose Edges", choices=gradio_app.get_edge(), multiselect=True, filterable=True)

add_node_button = gr.Button("Add Node")
add_edge_button = gr.Button("Add Edge")
delete_button = gr.Button("Delete")
refresh_button = gr.Button("Refresh")

node_attr1 = gr.Number(label="Panoid")
node_attr2 = gr.Number(label="Lat")
node_attr3 = gr.Number(label="Lng")
edge_node1 = gr.Dropdown(label="Start Node", choices=gradio_app.get_node(), multiselect=False)
edge_node2 = gr.Dropdown(label="End Node", choices=gradio_app.get_node(), multiselect=False)

with gr.Blocks() as demo:
    with gr.Row():
        with gr.Column():
            node_selection.render()
            edge_selection.render()
            delete_button.render()
        with gr.Column():
            graph_display = gr.HTML(gradio_app.display_graph() , label="Visualization")
            refresh_button.render()
    
    with gr.Row():
        with gr.Column():
            gr.Markdown("### Add Node")
            node_attr1.render()
            node_attr2.render()
            node_attr3.render()
            add_node_button.render()
        with gr.Column():
            gr.Markdown("### Add Edge")
            edge_node1.render()
            edge_node2.render()
            add_edge_button.render()
    
    add_node_button.click(fn=gradio_app.add_node, inputs=[node_attr1, node_attr2, node_attr3], outputs=[node_selection, edge_selection, edge_node1, edge_node2])
    add_edge_button.click(fn=gradio_app.add_edge, inputs=[edge_node1, edge_node2], outputs=[node_selection, edge_selection, edge_node1, edge_node2])
    delete_button.click(fn=gradio_app.delete, inputs=[node_selection, edge_selection], outputs=[node_selection, edge_selection, edge_node1, edge_node2])
    refresh_button.click(fn=gradio_app.display_graph, inputs=[node_selection, edge_selection], outputs=graph_display)

demo.launch()