# -*- coding:utf-8 -*-

from base_navigator import BaseNavigator
from map import get_street_view_image_url
from openai_agent import OpenAIAgent
from poe_agent import PoeAgent
from qa_agent import Oracle
from prompts.prompts import NAVIGATION_LVL_1, NAVIGATION_LVL_2, NAVIGATION_LVL_6
from util import AgentVisualization
from external_vision import VisionAnswering

# import config.map_config as map_config

import os 
import re
import json
import time

api_key = os.environ.get('GOOGLE_API_KEY')
base_dir = os.getcwd() # Get cwd current working directory


class Navigator(BaseNavigator):
    
    def __init__(self, 
                 config:str, 
                 oracle_config:str, 
                 answering_config:str, 
                 map_config: str|dict, 
                 task_config: str|dict,
                 show_info: bool=False): 
        
        if isinstance(map_config, dict):
            map_config_data = map_config
        elif isinstance(map_config, str):
            print(f"[init]Loading map config from {map_config}")
            with open(map_config, 'r') as f:
                map_config_data = json.load(f)
                
        if isinstance(task_config, dict):
            task_config_data = task_config
        elif isinstance(task_config, str):
            print(f"[init]Loading task config from {task_config}")
            with open(task_config, 'r') as f:
                task_config_data = json.load(f)
                
        super().__init__(task_config_data, map_config_data)
       
        print(f"[init]Loading config from {config}")
        with open(config, 'r') as f:
            self.config = json.load(f)

        print(f"[init]Loading oracle config from {oracle_config}")
        with open(oracle_config, 'r') as f:
            oracle_config_data = json.load(f)
            self.oracle = Oracle(oracle_config_data)
        
        print(f"[init]Loading vision config from {answering_config}")
        with open(answering_config, 'r') as f: 
            answering_config_data = json.load(f)
            self.answering = VisionAnswering(answering_config_data)
            
        if "vision_mode" in self.config: # vision_answering or url
            self.vision_mode = self.config["vision_mode"]
        else:
            self.vision_mode = "vision_answering"
        print(f"[init]Vision mode: {self.vision_mode}")    
        
        control_mode = self.config['mode']
        print(f"[init]Control mode: {control_mode}")
        self.offsets = [-90, -45, 0, 45, 90]
        if control_mode == "poe":
            self.client = PoeAgent(self.config) 
            self.action_mode = "poe_send_message"
        elif control_mode == "openai":
            self.client = OpenAIAgent(self.config)
            self.action_mode = "openai"
        elif control_mode == "human":
            self.action_mode = "human"
            
        if 'log_root' in map_config_data: # legacy
            self.log_root = map_config_data['log_root']
        else:
            log_dir_name = f"{time.strftime('%Y%m%d-%H%M%S')}_logs"
            self.log_root = os.path.join('output', 'logs', log_dir_name)
        os.makedirs(self.log_root, exist_ok=True)    
        
        self.log_infos = []
        self.show_info = show_info # show visualization and info in console
            
        # self.qa_client = QA_Agent()
        vis_silent = False if show_info else True
        target_nodes = [info["panoid"] for info in task_config_data["target_infos"]]
        self.visualization = AgentVisualization(self.graph, self.log_root, target_nodes=target_nodes, silent=vis_silent)

    def get_initial_prompt(self, start_config_file: str): #assuming this is a json config like overpasstask1 
        with open(start_config_file, 'r') as f: 
            content = json.load(f)
        
        start_lat = content['start']['lat']
        start_lon = content['start']['lon']
        target_lat = content['target']['lat']
        target_lon = content['target']['lon']

        def get_general_direction(start_lat, start_lon, target_lat, target_lon):
            if target_lon > start_lon:
                horizontal = "right" 
            elif target_lon < start_lon:
                horizontal = "left"  
            else:
                horizontal = None

            if target_lat > start_lat:
                vertical = "up"  
            elif target_lat < start_lat:
                vertical = "down" 
            else:
                vertical = None

            if horizontal and vertical:
                return f"{vertical} and {horizontal}"
            elif horizontal:
                return horizontal
            elif vertical:
                return vertical
            else:
                return "same location"

        general_direction = get_general_direction(start_lat, start_lon, target_lat, target_lon)
        path = f"https://maps.googleapis.com/maps/api/streetview?size=300x300&location={target_lat},{target_lon}&key=AIzaSyDv1zr5JJYKjv3MGIeYNEe5n1nP4gv2SSY&fov=90&heading=0&pitch=0&source=outdoor"
        target_summary = VisionAnswering.get_image_summary(path, False)
        return general_direction, target_summary
         
    def send_message(self, message: str, files=[]):
        return self.client.send_message(message, files)
    
    def parse_action(self, action_message: str):
        '''
        match [forward, left, right, turn_around, stop, lost]
        '''
        acton_space = ["forward", "left", "right", "turn_around", "stop", "lost"]
    
        match = re.search(r'\[Action:\s*(.*?)\]', action_message)
        if match: # try to match `[Action: ...]` first
            action = match.group(1)
            if action in acton_space:
                return action
        for action in acton_space: # if not matched, try to directly match the action in the message
            if action in action_message:
                return action
        
    def get_navigation_instructions(self, help_message=None, phase="new_state", supp_instructions=""): #phase = new_state, help
        if phase == "new_state":
            panoid, heading = self.graph_state 
            lat, lon = self.graph.get_node_coordinates(panoid)
            message = f"You are currently at {lat}, {lon} facing {heading}."
            message += "The five images below show the view in different directions, they are on your left, front-left, front, front-right, and right. Once you have decided which action to take, you can forget about the images."
            # message2 = "You can go through the following directions, to the new nodes: " + self.get_state_edges(self.graph_state)
            message3 = "You can take following action: " + self.show_state_info(self.graph_state)
            message4 = "Action: lost, ask for help.\nAction: stop, end the navigation."
            
            message += '\n' + message3 + '\n' + message4 + '\n' + supp_instructions
        elif phase == "help":
            message = help_message
        return message
    
    def get_navigation_action(self, image_urls, message: str, mode="poe_send_message"):    
        # vision information    
        if image_urls != [] and image_urls != None:
            if self.vision_mode == "url":
                image_feed = image_urls
            elif self.vision_mode == "vision_answering":
                image_feed = []
                map_of_summaries = self.answering.order_image_summaries(self.offsets, image_urls, self.help_message, False)
                new_message = ""
                for k, v in map_of_summaries.items(): 
                    new_message += f"At your {k} heading, we see {v}."
                message += new_message
            else:
                raise ValueError("Invalid vision mode") 
            
        if self.show_info:
            print("*"*50, "[get_navigation_action] System input:")
            print("Getting navigation action")
            print(f"Message: {message}")
            print(f"Image features: {image_urls}")
            print("*"*50)   
                    
        if mode == "poe_send_message":
            chunk = self.send_message(message=message, files=image_feed)
            action_message = chunk["text"]
            action = self.parse_action(action_message)
            if self.show_info:
                print("="*50, "[get_navigation_action] Agent output:")
                print(f"Action message: {action_message}")
                print(f"Action: {action}")
                print("="*50)
        elif mode == "openai":
            action_message = self.send_message(message, files=image_feed)
            action = self.parse_action(action_message)
            if self.show_info:
                print("="*50, "[get_navigation_action] Agent output:")
                print(f"Action message: {action_message}")
                print(f"Action: {action}")
                print("="*50)
        elif mode == "human":
            action = input("Enter the move: ")
            action_message = f"[Action: {action}] is human mode"
        else:
            raise ValueError("Invalid mode")
        return action, action_message
    
    def get_image_feature(self, graph_state, mode="human"):
        '''
        return_type: "List[url]"
        '''     
        panoid, heading = graph_state
        lat, lon = self.graph.nodes[panoid].coordinate
        if self.show_info:
            print("*"*50, "[get_image_feature] System:")
            print(f"Getting image features for {lat}, {lon} facing {heading}")
            print("*"*50)

        image_urls = []
        for offset in self.offsets:
            heading_image = (heading + offset) % 360
            image_url = get_street_view_image_url(lat, lon, api_key, heading_image)
            image_urls.append(image_url)

        return image_urls 
            
    def ask_for_help(self, mode="human"): 
        '''
        return answer from the oracle
        TODO -> read human input should be able to work / gpt4o model for  
        '''
        # question from QA agent
        message = self.oracle.question
        self.log_info["qa_messages"]['answer'].append(message)
        
        # get question from main agent
        if mode == "poe_send_message":
            chunk = self.send_message(message=message)
            question = chunk['text']
        elif mode == "openai":
            question = self.send_message(message)
        elif mode == "human":
            question = input("Enter the question: ")
        else:
            raise ValueError("Invalid mode")
        self.log_info["qa_messages"]['question'].append(question)
       
        # get answer from QA agent
        help_message = self.oracle.get_answer(question)
        return help_message
    
    def get_agent_vis(self, graph_state):
        panoid, heading = graph_state
        candidate_nodes = self.graph.get_candidate_nodes(panoid, heading)
        candidate_nodeid = [node.panoid for node in candidate_nodes]
        agent_vis_file = self.visualization.update(panoid, candidate_nodeid)
        return agent_vis_file

    def forward(self): 
        start_graph_state = (self.start_node, self.task_config.get("start_heading", 0))
        self.graph_state = start_graph_state
        self.graph_state = self.fix_heading(self.graph_state)
        print(f"[forward] Heading {start_graph_state[1]} -> {self.graph_state[1]}")
        self.help_message = None
        self.visualization.init_current_node(self.graph_state[0])

        instruction_ctn = 0
        
        # initial state
        step = 0
        self.log_info = {'step': step, 'log_root': self.log_root}
        self.log_info["current_state"] = self.graph_state
        self.log_info["agent_vis"] = self.get_agent_vis(self.graph_state)
        self.log_info["image_urls"] = self.get_image_feature(self.graph_state, mode=self.action_mode)
        self.log_info["action"] = "start"
        self.log_info["message"] = ["Start navigation"]
        yield self.log_info
        
        step += 1
        while True:     
            if step > self.log_info['step']: # new state, reset log_info
                self.log_infos.append(self.log_info)
                self.log_info = {'step': step, 'log_root': self.log_root, 'image_urls': self.log_info['image_urls']}
            
            # get action/move
            if self.help_message: # is asking for help, previous action is lost
                message = self.get_navigation_instructions(self.help_message, phase="help") # message = help_message
                self.help_message = None
                action, action_message = self.get_navigation_action([], message, mode=self.action_mode)
            else:
                image_urls = self.get_image_feature(self.graph_state, mode=self.action_mode)
                self.log_info["image_urls"] = image_urls
                message = self.get_navigation_instructions(supp_instructions= "" if instruction_ctn >= len(NAVIGATION_LVL_6) else NAVIGATION_LVL_6[instruction_ctn])
                instruction_ctn += 1
                action, action_message = self.get_navigation_action(image_urls, message, mode=self.action_mode)
                
            if 'message' not in self.log_info:
                self.log_info['message'] = []
            self.log_info["message"].append(message)
            self.log_info["action"] = action
            self.log_info["action_message"] = action_message
                
            # if action == 'stop': 
            #     step += 1
            #     print("Action stop is chosen")
            # elif action == 'lost':
            if action == 'lost':
                if 'qa_messages' not in self.log_info:
                    self.log_info['qa_messages'] = {'question': [], 'answer': []}
                self.log_info['qa_messages']['question'].append('lost')
                self.help_message = self.ask_for_help(mode=self.action_mode)
                self.log_info['qa_messages']['answer'].append(self.help_message)
            else:
                step += 1
                err_message = self.step(action)
                if err_message != '':  # if has err, pass err message as help message
                    self.help_message = err_message
                    self.help_message += "\n"
                    self.help_message += self.log_info["message"][0] # instruction message
                    
            # update visualization
            agent_vis_file = self.get_agent_vis(self.graph_state)
            self.log_info["current_state"] = self.graph_state
            self.log_info["agent_vis"] = agent_vis_file
                                    
            if self.show_info: 
                print(self.show_state_info(self.graph_state))
                
            if action == 'stop' and self.check_arrival_all():
                
                self.log_infos.append(self.log_info)
                with open(os.path.join(self.log_root, "log_infos.json"), 'w') as f:
                    json.dump(self.log_infos, f)    
                    
                self.log_info["over"] = True
                    
            yield self.log_info
        
def show_graph_info(graph):
    max_neighbors = 0
    max_neighbors_node = None
    for node in graph.nodes.values():
        neighbors_num = len(node.neighbors)
        if neighbors_num > max_neighbors:
            max_neighbors = neighbors_num
            max_neighbors_node = node
    print(f"Max neighbors: {max_neighbors}, node: {max_neighbors_node.panoid}")
            
            

if __name__ == "__main__":   

    navi_config = r"config\human_test_navi.json"
    # navi_config = os.path.join("config", "openai_test_navi_3.json")
    # navi_config = r"config\poe_test_navi.json"
    oracle_config = os.path.join("config", "human_test_oracle.json")
    vision_config = os.path.join("config", "human_test_vision.json")
    map_config = os.path.join("config", "overpass_streetmap_map.json")
    task_config = os.path.join("config", "overpass_task1.json")

    navigator = Navigator(config=navi_config, 
                          oracle_config=oracle_config, 
                          answering_config=vision_config, 
                          map_config=map_config, 
                          task_config=task_config,
                          show_info=True)
    task = navigator.forward(('65303689', 0))
    while True:
        info = next(task)
        print(info)
        action = info["action"]
        if info.get("over", False):
            break
    

        
    