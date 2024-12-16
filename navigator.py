# -*- coding:utf-8 -*-

import os 
import re
import json
import time
import argparse

from base_navigator import BaseNavigator
from graph_loader import get_street_view_image_url

from oracle import Oracle
from external_vision import VisionAnswering
from evaluator import AgentEvaluator

from prompts.prompts import NAVIGATION_LVL_1, NAVIGATION_LVL_2, NAVIGATION_LVL_6
from util.visualize_map import AgentVisualization

try:
    from testing_agents.openai_agent import OpenAIAgent
except ImportError:
    print("OpenAI agent is not available in your environment. Not importing OpenAIAgent.")

try:
    from testing_agents.poe_agent import PoeAgent
except ImportError:
    print("Poe agent is not available in your environment. Not importing PoeAgent.")

try:
    from testing_agents.anthropic_agent import AnthropicAgent
except ImportError:
    print("Anthropic agent is not available in your environment. Not importing AnthropicAgent.")

try:
    from testing_agents.gemini_agent import GeminiAgent
except ImportError:
    print("Gemini agent is not available in your environment. Not importing GeminiAgent.")

try:
    from testing_agents.mistral_agent import MistralaiAgent
except ImportError:
    print("Mistralai agent is not available in your environment. Not importing MistralaiAgent.")

api_key = os.environ.get('GOOGLE_API_KEY')
print(api_key)
base_dir = os.getcwd() # Get cwd current working directory

class Navigator(BaseNavigator):
    
    def __init__(self, 
                 config:str, 
                 answering_config:str, 
                 map_config: str|dict,
                 eval_config: str, 
                 task_config: str|dict,
                 show_info: bool=False,
                 output_path: str='output'): 
        
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
          
        # insert target names into policy    
        target_names = [info["name"] for info in task_config_data["target_infos"]]
        target_names = ", ".join(target_names)
        self.config["policy"] = self.config["policy"].replace("<<<target_name>>>", target_names)
        print(f"[init]Policy/Init prompt: {self.config['policy']}")

        print(f"[init]Loading oracle config")
        self.oracle = Oracle()
        
        print(f"[init]Loading vision config from {answering_config}")
        with open(answering_config, 'r') as f: 
            answering_config_data = json.load(f)
            self.answering = VisionAnswering(answering_config_data)
            
        if "vision_mode" in self.config: # vision_answering or url
            self.vision_mode = self.config["vision_mode"]
        else:
            self.vision_mode = "vision_answering"
        print(f"[init]Vision mode: {self.vision_mode}")

        with open(eval_config, 'r') as f:
            eval_config_data = json.load(f)
            self.evaluator = AgentEvaluator(eval_config_data)
                
        self.offsets = [-90, -45, 0, 45, 90]
        
        control_mode = self.config['mode']
        print(f"[init]Control mode: {control_mode}")
        if control_mode == "poe":
            self.client = PoeAgent(self.config) 
            self.action_mode = "agent"
        elif control_mode == "openai":
            self.client = OpenAIAgent(self.config)
            self.action_mode = "agent"
        elif control_mode == "anthropic":
            self.client = AnthropicAgent(self.config)
            self.action_mode = "agent"
        elif control_mode == "gemini":
            self.client = GeminiAgent(self.config)
            self.action_mode = "agent"
        elif control_mode == "mistral":
            self.client = MistralaiAgent(self.config)
            self.action_mode = "agent"
        elif control_mode == "human":
            self.action_mode = "human"
            
        if 'log_root' in map_config_data: # legacy
            self.log_root = map_config_data['log_root']
        else:
            log_dir_name = f"{time.strftime('%Y%m%d-%H%M%S')}_logs"
            self.log_root = os.path.join(output_path, 'logs', log_dir_name)
        os.makedirs(self.log_root, exist_ok=True)    
        
        self.log_infos = [{"config": config, "map_config": map_config_data, "task_config": task_config_data}]
        self.show_info = show_info # show visualization and info in console
            
        vis_silent = False if show_info else True
        target_nodes = [info["panoid"] for info in task_config_data["target_infos"]]
        self.visualization = AgentVisualization(self.graph, self.log_root, google_api=api_key, target_nodes=target_nodes, silent=vis_silent)

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
        match [forward, left, right, turn_around, stop, ask]
        '''
        acton_space = ["forward", "left", "right", "turn_around", "stop", "ask"]
    
        match = re.search(r'\[Action:\s*(.*?)\]', action_message)
        if match: # try to match `[Action: ...]` first
            action = match.group(1)
            if action in acton_space:
                return action
        for action in acton_space: # if not matched, try to directly match the action in the message
            if action in action_message:
                return action
        return "You didn't provide a valid action, please try again with [Action: ...]"
        
    def get_navigation_instructions(self, help_message=None, phase="new_state", supp_instructions=""): #phase = new_state, help
        if phase == "new_state":
            panoid, heading = self.graph_state 
            lat, lon = self.graph.get_node_coordinates(panoid)
            message = ""
            # message += f"You are currently at {lat}, {lon} facing {heading}."
            message += "The five images below show the view in different directions, they are on your left, front-left, front, front-right, and right."
            # message2 = "You can go through the following directions, to the new nodes: " + self.get_state_edges(self.graph_state)
            message3 = "You can take following action, only these actions are available in this position: " + self.show_state_info(self.graph_state)
            message4 = "[Action: ask], ask for more information.\n[Action: stop], report arrival."
            
            message += '\n' + message3 + '\n' + message4 + '\n' + supp_instructions
        elif phase == "help":
            message = help_message
        return message
    
    def get_navigation_action(self, image_urls, message: str, mode="human"):    
        # vision information 
        image_feed = []   
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
        
        if mode == "agent":
            action_message = self.send_message(message, files=image_feed)
            action = self.parse_action(action_message)
            if self.show_info:
                print("="*50, "[get_navigation_action] Agent output:")
                print(f"Action message: {action_message}")
                print(f"Action: {action}")
                print("="*50)
        elif mode == "human":
            action_message = input("Enter the move: ")
            action = self.parse_action(action_message)
        else:
            raise ValueError("Invalid mode")
        return action, action_message
    
    def get_image_feature(self, graph_state):
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
        if mode == "agent":
            question = self.send_message(message)
        elif mode == "human":
            question = input("Enter the question: ")
        else:
            raise ValueError("Invalid mode")
        self.log_info["qa_messages"]['question'].append(question)
       
        # get answer from QA agent
        world_states, clues = self.collect_observations()
        self.oracle.update_observations(
            world_states=world_states, 
            clues=clues
        )
        help_message = self.oracle.get_answer(question)
        if self.show_info:
            print(f"The result of help message is: {help_message}")
        return help_message
    
    def get_agent_vis(self, graph_state):
        panoid, heading = graph_state
        candidate_nodes = self.graph.get_candidate_nodes(panoid, heading)
        candidate_nodeid = [node.panoid for node in candidate_nodes]
        agent_vis_file = self.visualization.update(panoid, candidate_nodeid)
        return agent_vis_file
    
    def navigation_log(self, step, agent_response=None, shortest_path=None, forward_ctn=None, ask_ctn=None, save_json=True):
        if (agent_response is not None and 
            shortest_path is not None and 
            forward_ctn is not None and 
            ask_ctn is not None):
            try:
                num_question, num_steps, action_score, question_score = self.evaluator.calculate_score(agent_response, shortest_step=shortest_path, num_steps=forward_ctn, num_q=ask_ctn, debug=True)
            except Exception as e:
                print(f"An error occurred while calculating the score: {e}")
    
                # Optionally set default values to avoid breaking later code
                num_question = num_steps = action_score = question_score = None
                
            self.log_info["metrics"] = {"num_question": num_question, 
                                        "num_steps": num_steps, 
                                        "action_score": action_score, 
                                        "question_score": question_score}
            self.log_info["forward_ctn"] = forward_ctn
            self.log_info["ask_ctn"] = ask_ctn
        
        self.log_info["arrival_info"] = self.collect_arrival_info()
        logs_save = self.log_infos
        logs_save.append(self.log_info)
        
        if save_json:
            with open(os.path.join(self.log_root, f"log_infos_{step}.json"), 'w') as f:
                json.dump(logs_save, f)    
        
        return self.log_info

    def forward(self): 
        try:
            start_graph_state = (self.start_node, self.task_config.get("start_heading", 0))
            self.graph_state = start_graph_state
            self.graph_state = self.fix_heading(self.graph_state)
            print(f"[forward] Heading {start_graph_state[1]} -> {self.graph_state[1]}")
            self.help_message = None
            self.visualization.init_current_node(self.graph_state[0])

            
            # initial state
            step = 0
            instruction_ctn = 0
            forward_ctn = 0
            ask_ctn = 0
            agent_response = []
            world_states, clues = self.collect_observations()
            shortest_path = world_states["path_action"]
            print("Path to Target: ", world_states["path_action"])

            self.log_info = {'step': step, 'log_root': self.log_root}
            self.log_info["current_state"] = self.graph_state
            self.log_info["agent_vis"] = self.get_agent_vis(self.graph_state)
            self.log_info["image_urls"] = self.get_image_feature(self.graph_state)
            self.log_info["action"] = "start"
            self.log_info["action_message"] = "start"
            self.log_info["shortest_path"] = shortest_path
            
            self.log_info["message"] = [self.config["policy"]]
            self.log_info["target_status"] = [info["status"] for info in self.target_infos]
            yield self.log_info
            
            step += 1
            while True:     
                if step > self.log_info['step']: # new state, reset log_info
                    self.log_infos.append(self.log_info)
                    self.log_info = {'step': step, 'log_root': self.log_root, 'image_urls': self.log_info['image_urls']}
                
                # get action/move
                if self.help_message: # is asking for help, previous action is ask
                    message = self.get_navigation_instructions(self.help_message, phase="help") # message = help_message
                    self.help_message = None
                    action, action_message = self.get_navigation_action([], message, mode=self.action_mode)
                else:
                    image_urls = self.get_image_feature(self.graph_state)
                    self.log_info["image_urls"] = image_urls
                    message = self.get_navigation_instructions(supp_instructions= "" if instruction_ctn >= len(NAVIGATION_LVL_1) else NAVIGATION_LVL_1[instruction_ctn])
                    instruction_ctn += 1
                    action, action_message = self.get_navigation_action(image_urls, message, mode=self.action_mode)
                
                agent_response.append(("Context: " + message, "Agent Action: " + action, "Agent Response: " + action_message))
                forward_ctn += 1 if action == "forward" else 0
                ask_ctn += 1 if action == "ask" else 0
                self.log_info["forward_ctn"] = forward_ctn
                self.log_info["ask_ctn"] = ask_ctn
                
                if 'message' not in self.log_info:
                    self.log_info['message'] = []
                self.log_info["message"].append(message)
                self.log_info["action"] = action
                self.log_info["action_message"] = action_message
                    
                if action == 'ask':
                    if 'qa_messages' not in self.log_info:
                        self.log_info['qa_messages'] = {'question': [], 'answer': []}
                    self.log_info['qa_messages']['question'].append('ask')
                    self.help_message = self.ask_for_help(mode=self.action_mode)
                    self.help_message += "\n" + "If you have further questions, please reply [Action: ask] now, then give you question in the next round."
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
                self.log_info["target_status"] = [info["status"] for info in self.target_infos]
                                        
                if self.show_info: 
                    print(self.show_state_info(self.graph_state))
                    
                # if achive all target or reach max step, end the navigation
                if (action == 'stop' and self.check_arrival_all()) or step > self.max_step:
                    print("DONE")
                    self.log_info["over"] = True
                    self.navigation_log(step, 
                                        agent_response=agent_response, 
                                        shortest_path=shortest_path, 
                                        forward_ctn=forward_ctn, 
                                        ask_ctn=ask_ctn, 
                                        save_json=True)
            
                yield self.log_info

        except Exception as e:
            print(f"Task failed due to {e}")

            try:
                # save record
                self.log_info["over"] = "Error"
                self.navigation_log(step, 
                                    agent_response=agent_response, 
                                    shortest_path=shortest_path, 
                                    forward_ctn=forward_ctn, 
                                    ask_ctn=ask_ctn, 
                                    save_json=True)
            except:
                print(f"Error happened before logging started. No log output generated")
            
            raise e

        
def show_graph_info(graph):
    max_neighbors = 0
    max_neighbors_node = None
    for node in graph.nodes.values():
        neighbors_num = len(node.neighbors)
        if neighbors_num > max_neighbors:
            max_neighbors = neighbors_num
            max_neighbors_node = node
    print(f"Max neighbors: {max_neighbors}, node: {max_neighbors_node.panoid}")

def main(args):
    navi_config = os.path.join("config", "navi", args.navi) \
        if args.navi else os.path.join("config", "navi", "human_test_navi.json")
    vision_config = os.path.join("config", "vision", args.vision) \
        if args.vision else os.path.join("config", "vision", "openai_vision.json")
    map_config = os.path.join("config", "map", args.map) \
        if args.map else os.path.join("config", "map", "touchdown_streetmap.json")
    eval_config = os.path.join("config", "eval", args.eval) \
        if args.eval else os.path.join("config", "eval", "evaluator.json")
    task_config = os.path.join("config", "task", args.task) \
        if args.task else os.path.join("config", "task", "overpass_task1.json")
    output_path = args.output

    navigator = Navigator(config=navi_config, 
                          answering_config=vision_config, 
                          map_config=map_config,
                          eval_config=eval_config, 
                          task_config=task_config,
                          output_path=output_path,
                          show_info=False)

    task = navigator.forward()
    
    while True:
        info = next(task)
        print(info)
        action = info["action"]
        if info.get("over", False):
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="All navigation configs")

    parser.add_argument('--navi', type=str, help='Navigation config in config/navi/*.json')
    parser.add_argument('--vision', type=str, help='Vision config in config/vision/*.json')
    parser.add_argument('--map', type=str, help='Map config in config/map/*.json')
    parser.add_argument('--eval', type=str, help='Eval config in config/eval/*.json')
    parser.add_argument('--task', type=str, help='Task config in config/task/*.json')
    parser.add_argument('--output', type=str, default='output', help='Output path; Default to output/')

    args = parser.parse_args()

    main(args)
