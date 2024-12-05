from poe_navigator import Navigator
import gradio as gr
import matplotlib.pyplot as plt
import os
import sys

def update_config_files():
    new_navi_choices = [file.split('.')[0] for file in os.listdir(config_root) if "navi" in file]
    new_vision_choices = [file.split('.')[0] for file in os.listdir(config_root) if "vision" in file]
    new_oracle_choices = [file.split('.')[0] for file in os.listdir(config_root) if "oracle" in file]
    new_map_choices = [file.split('.')[0] for file in os.listdir(config_root) if "map" in file]
    return gr.update(value=[], choices=new_navi_choices), gr.update(value=[], choices=new_vision_choices), gr.update(value=[], choices=new_oracle_choices), gr.update(value=[], choices=new_map_choices)

config_root = "config"

navi_config_choices = [file.split('.')[0] for file in os.listdir(config_root) if "navi" in file]
navi_config_selection = gr.Dropdown(value=[],label="Navigator Config", choices=navi_config_choices, max_choices=1, multiselect=True, interactive=True)

vision_config_choices = [file.split('.')[0] for file in os.listdir(config_root) if "vision" in file]
vision_config_selection = gr.Dropdown(value=[],label="Vision Config", choices=vision_config_choices, max_choices=1, multiselect=True, interactive=True)

oracle_config_choices = [file.split('.')[0] for file in os.listdir(config_root) if "oracle" in file]
oracle_config_selection = gr.Dropdown(value=[],label="Oracle Config", choices=oracle_config_choices, max_choices=1, multiselect=True, interactive=True)

map_config_choices = [file.split('.')[0] for file in os.listdir(config_root) if "map" in file]
map_config_selection = gr.Dropdown(value=[],label="Map Config", choices=map_config_choices, max_choices=1, multiselect=True, interactive=True)
    
start_button = gr.Button("Start!")
refresh_button = gr.Button("Refresh")
last_step_button = gr.Button("Last Step")
next_step_button = gr.Button("Next Step")

total_steps_num = gr.Number(label="Total Steps", value=0, interactive=False)
current_step_num = gr.Number(label="Current Step", value=0, interactive=False)

init_prompt_text = gr.Textbox(label="Initial Prompt", interactive=False)
step_prompt_text = gr.Textbox(label="Step Prompt", interactive=False)

position_text = gr.Textbox(label="Position", interactive=False)
heading_text = gr.Textbox(label="Heading", interactive=False)

action_text = gr.Textbox(label="Action", interactive=False)
log_root_text = gr.Textbox(label="Log Root", interactive=False)

qa_chatbot = gr.Chatbot(type="messages", label="QA System")

agen_vis_image = gr.Image(label="Agent Visualization", interactive=False)
vision_input_images = gr.Gallery(label="Vision Input", show_label=True, columns=5, rows=1, height="auto", interactive=False)

with gr.Blocks() as demo:
    with gr.Row(equal_height=True):
        navi_config_selection.render()
        vision_config_selection.render()
        oracle_config_selection.render()
        map_config_selection.render()
        refresh_button.render()
    with gr.Row(equal_height=True):
        start_button.render()
        total_steps_num.render()
        current_step_num.render()
    with gr.Row():
        with gr.Column(scale=1):
            position_text.render()
            heading_text.render()
            step_prompt_text.render()
            action_text.render()
            qa_chatbot.render()
        with gr.Column(scale=2):
            agen_vis_image.render()
            with gr.Row():
                last_step_button.render()
                next_step_button.render()
    with gr.Row():
        vision_input_images.render()
    with gr.Row():
        init_prompt_text.render()
    with gr.Row():
        log_root_text.render()
        
    refresh_button.click(fn=update_config_files, inputs=None, outputs=[navi_config_selection, vision_config_selection, oracle_config_selection, map_config_selection])
       

if __name__ == "__main__":
    demo.launch()



# navi_config = "config/human_test_navi.json"
# oracle_config = os.path.join("config", "human_test_oracle.json")
# vision_config = "config/human_test_vision.json"
# map_config = "config/map_config.json"

# navigator = Navigator(config=navi_config, oracle_config=oracle_config, answering_config=vision_config, map_config=map_config,show_info=True)
# navigator.forward(('65303689', 0))