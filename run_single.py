from poe_navigator import Navigator
import gradio as gr
from gradio import ChatMessage
import matplotlib.pyplot as plt
import os
import sys
import json

def update_config_files():
    new_navi_choices = [file.split('.')[0] for file in os.listdir(config_root) if "navi" in file]
    new_vision_choices = [file.split('.')[0] for file in os.listdir(config_root) if "vision" in file]
    new_oracle_choices = [file.split('.')[0] for file in os.listdir(config_root) if "oracle" in file]
    new_map_choices = [file.split('.')[0] for file in os.listdir(config_root) if "map" in file]
    new_task_choices = [file.split('.')[0] for file in os.listdir(config_root) if "task" in file]   
    return gr.update(value=[], choices=new_navi_choices), gr.update(value=[], choices=new_vision_choices), gr.update(value=[], choices=new_oracle_choices), gr.update(value=[], choices=new_map_choices), gr.update(value=[], choices=new_task_choices)

def start_navigation(navi_config, vision_config, oracle_config, map_config, task_config):
    navi_config = os.path.join(config_root, navi_config[0]+".json")
    oracle_config = os.path.join(config_root, oracle_config[0]+".json")
    vision_config = os.path.join(config_root, vision_config[0]+".json")
    map_config = os.path.join(config_root, map_config[0]+".json")
    task_config = os.path.join(config_root, task_config[0]+".json")
    
    global navigator
    navigator = Navigator(config=navi_config, 
                          oracle_config=oracle_config, 
                          answering_config=vision_config, 
                          map_config=map_config,
                          task_config=task_config,
                          show_info=False)
    
    with open(navi_config, "r") as f:
        navi_config_data = json.load(f)
    init_prompt = navi_config_data["policy"]
    
    
    return init_prompt, gr.update(interactive=False), gr.update(interactive=False), gr.update(interactive=False), gr.update(interactive=False), gr.update(interactive=False), gr.update(interactive=False), gr.update(interactive=False)

def run_navigation():
    global navigator, infos_state

    task = navigator.forward()
    
    while True:
        info = next(task)
        step = info["step"]
        
        if step >= len(infos_state):
            infos_state.append(info)
            assert len(infos_state) == step + 1
        else:
            infos_state[step] = info
    
        action = info["action"]
        yield step
        if action == "stop":
            break
    return step
    
def step_button_click(current_step, step_change):
    new_current_step = current_step + step_change
    global infos_state
    if new_current_step < 0 or new_current_step >= len(infos_state):
        print("Invalid step")
        return current_step
    return new_current_step
    

def update_current_step(current_step):
    global infos_state
    if current_step < 0 or current_step >= len(infos_state):
        print("Invalid step")
        raise ValueError("Invalid step")
    info = infos_state[current_step]
    action = info["action"]
    panoid = info["current_state"][0]
    heading = info["current_state"][1]
    agent_vis_path = info["agent_vis"]
    log_root = info["log_root"]
    
    messages = info["message"]
    message = "\n".join(messages)
    
    vision_input_images = info["image_urls"]
    if "qa_messages" in info:
        question = info["qa_messages"]["question"]
        answer = info["qa_messages"]["answer"]
        qa_messages = []
        for i in range(len(question)):
            qa_messages.append(dict(role="user", content=question[i]))
            qa_messages.append(dict(role="assistant", content=answer[i]))
    else:
        qa_messages = gr.skip()
    return qa_messages, panoid, heading, message, action, log_root, agent_vis_path, vision_input_images

config_root = "config"
navigator = None
infos_state = []

auto_update_state = gr.State(value=True)

navi_config_choices = [file.split('.')[0] for file in os.listdir(config_root) if "navi" in file]
navi_config_selection = gr.Dropdown(value=[],label="Navigator Config", choices=navi_config_choices, max_choices=1, multiselect=True, interactive=True)

vision_config_choices = [file.split('.')[0] for file in os.listdir(config_root) if "vision" in file]
vision_config_selection = gr.Dropdown(value=[],label="Vision Config", choices=vision_config_choices, max_choices=1, multiselect=True, interactive=True)

oracle_config_choices = [file.split('.')[0] for file in os.listdir(config_root) if "oracle" in file]
oracle_config_selection = gr.Dropdown(value=[],label="Oracle Config", choices=oracle_config_choices, max_choices=1, multiselect=True, interactive=True)

map_config_choices = [file.split('.')[0] for file in os.listdir(config_root) if "map" in file]
map_config_selection = gr.Dropdown(value=[],label="Map Config", choices=map_config_choices, max_choices=1, multiselect=True, interactive=True)

task_config_choices = [file.split('.')[0] for file in os.listdir(config_root) if "task" in file]
task_config_selection = gr.Dropdown(value=[],label="Task Config", choices=task_config_choices, max_choices=1, multiselect=True, interactive=True)
    
start_button = gr.Button("Start!")
refresh_button = gr.Button("Refresh")
last_step_button = gr.Button("Last Step")
next_step_button = gr.Button("Next Step")

total_steps_num = gr.Number(label="Total Steps", value=0, interactive=False)
current_step_num = gr.Number(label="Current Step", value=-1, interactive=False)

init_prompt_text = gr.Textbox(label="Initial Prompt", interactive=False)
step_prompt_text = gr.Textbox(label="Step Prompt", interactive=False)

position_text = gr.Textbox(label="Position", interactive=False)
heading_text = gr.Textbox(label="Heading", interactive=False)

action_text = gr.Textbox(label="Action", interactive=False)
log_root_text = gr.Textbox(label="Log Root", interactive=False)

qa_chatbot = gr.Chatbot(type="messages", label="QA System")

agent_vis_image = gr.Image(label="Agent Visualization", interactive=False)
vision_input_images = gr.Gallery(label="Vision Input", show_label=True, columns=5, rows=1, height="auto", interactive=False)

with gr.Blocks() as demo:
    with gr.Row(equal_height=True):
        navi_config_selection.render()
        vision_config_selection.render()
        oracle_config_selection.render()
        map_config_selection.render()
        task_config_selection.render()
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
            agent_vis_image.render()
            with gr.Row():
                last_step_button.render()
                next_step_button.render()
    with gr.Row():
        vision_input_images.render()
    with gr.Row():
        init_prompt_text.render()
    with gr.Row():
        log_root_text.render()
        
    refresh_button.click(fn=update_config_files, inputs=None, outputs=[navi_config_selection, vision_config_selection, oracle_config_selection, map_config_selection, task_config_selection])
    
    start_button.click(fn=start_navigation, 
                       inputs=[navi_config_selection, vision_config_selection, oracle_config_selection, map_config_selection, task_config_selection], 
                       outputs=[init_prompt_text, start_button, navi_config_selection, vision_config_selection, oracle_config_selection, map_config_selection, task_config_selection, refresh_button]).then(run_navigation, inputs=None, outputs=[total_steps_num])
    
    last_step_button.click(fn=step_button_click, inputs=[current_step_num, gr.Number(-1)], outputs=[current_step_num])
    next_step_button.click(fn=step_button_click, inputs=[current_step_num, gr.Number(1)], outputs=[current_step_num])
       
    current_step_num.change(fn=update_current_step, inputs=[current_step_num], outputs=[qa_chatbot, position_text, heading_text, step_prompt_text, action_text, log_root_text, agent_vis_image, vision_input_images])

if __name__ == "__main__":
    demo.launch()



# navi_config = "config/human_test_navi.json"
# oracle_config = os.path.join("config", "human_test_oracle.json")
# vision_config = "config/human_test_vision.json"
# map_config = "config/map_config.json"

# navigator = Navigator(config=navi_config, oracle_config=oracle_config, answering_config=vision_config, map_config=map_config,show_info=True)
# navigator.forward(('65303689', 0))