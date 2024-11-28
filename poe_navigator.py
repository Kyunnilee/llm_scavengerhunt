from base_navigator import BaseNavigator
import json
from map import get_street_view_image_url
from openai_agent import OpenAIAgent
from poe_agent import PoeAgent
from prompts.prompts import NAVIGATION_LVL_1, NAVIGATION_LVL_2, NAVIGATION_LVL_6
import os 
import config.map_config as map_config
import re
from util import AgentVisualization
from external_vision import VisionAnswering

api_key = os.environ.get('GOOGLE_API_KEY')
base_dir = os.getcwd() # Get cwd current working directory


class Navigator(BaseNavigator):
    
    def __init__(self, config, oracle_config, answering_config, show_info=False): 
        super().__init__()
        
        self.image_root = map_config.data_paths['image_root']
        self.show_info = show_info
       
        print(f"Loading config from {config}")
        with open(config, 'r') as f:
            self.config = json.load(f)

        print(f"Loading oracle config from {oracle_config}")
        with open(oracle_config, 'r') as f:
            oracle_config_data = json.load(f)
            self.oracle = Oracle(oracle_config_data)
        
        with open(answering_config, 'r') as f: 
            answering_config_data = json.load(f)
            self.answering = VisionAnswering(answering_config_data)

        control_mode = self.config['mode']
        print(f"Control mode: {control_mode}")
        self.offsets = [-90, -45, 0, 45, 90]
        if control_mode == "poe":
            self.client = PoeAgent(self.config) 
            self.action_mode = "poe_send_message"
        elif control_mode == "openai":
            self.client = OpenAIAgent(self.config)
            self.action_mode = "openai"
        elif control_mode == "human":
            self.action_mode = "human"
        
        self.qa_client = QA_Agent()

        # if show_info:
        #     self.visualization = AgentVisualization(self.graph, self.image_root)
    
    def send_message(self, message: str, files=[]):
        return self.client.send_message(message, files)
    
    def parse_action(self, action_message: str):
        '''
        match [forward, left, right, stop, lost]
        '''
        acton_space = ["forward", "left", "right", "turn_around", "stop", "lost"]
    
        match = re.search(r'\[Action:\s*(.*?)\]', action_message)
        if match: # try to match `[Action: ...]` first
            print(f"Match: {match.group(1)}")
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
        if self.show_info:
            print("*"*50, "[get_navigation_action] System input:")
            print("Getting navigation action")
            print(f"Message: {message}")
            print(f"Image features: {image_urls}")
            print("*"*50)
            
        if mode == "poe_send_message":
            #False here is for the is_debug flag // Can remove 
            map_of_summaries = self.answering.order_image_summaries(self.offsets, image_urls, False)
            new_message = ""
            for k, v in map_of_summaries.items(): 
                new_message += f"At your {k} heading, we see {v}."
            message += new_message
            print(message)
            chunk = self.send_message(message=message)
            action_message = chunk["text"]
            print(action_message)
            action = self.parse_action(action_message)
            if self.show_info:
                print("="*50, "[get_navigation_action] Agent output:")
                print(f"Action message: {action_message}")
                print(f"Action: {action}")
                print("="*50)
        elif mode == "openai":
            action_message = self.send_message(message)
            action = self.parse_action(action_message)
            if self.show_info:
                print("="*50, "[get_navigation_action] Agent output:")
                print(f"Action message: {action_message}")
                print(f"Action: {action}")
                print("="*50)
        elif mode == "human":
            action = input("Enter the move: ")
        return action
    
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
        message = self.oracle.question
        if mode == "poe_send_message":
            chunk = self.send_message(message=message)
            question = chunk['text']
        elif mode == "openai":
            question = self.send_message(message)
        elif mode == "human":
            question = input("Enter the question: ")
       
        help_message = self.oracle.get_answer(question)
        return help_message

    def forward(self, start_graph_state): 
        self.graph_state = start_graph_state
        self.graph_state = self.fix_heading(self.graph_state)
        print(f"[forward] Heading {start_graph_state[1]} -> {self.graph_state[1]}")
        self.help_message = None
        self.visualization.init_current_node(self.graph_state[0])

        i = 0
        while True: 
            if self.show_info: 
                current_nodeid = self.graph_state[0]
                heading = self.graph_state[1]
                candidate_nodes = self.graph.get_candidate_nodes(current_nodeid, heading)
                candidate_nodeid = [node.panoid for node in candidate_nodes]
                
                self.visualization.update(current_nodeid, candidate_nodeid)
            # get action/move
            if self.help_message: # is asking for help
                message = self.get_navigation_instructions(self.help_message, phase="help")
                self.help_message = None
                action = self.get_navigation_action([], message, mode=self.action_mode)
            else:
                image_urls = self.get_image_feature(self.graph_state, mode=self.action_mode)
                message = self.get_navigation_instructions(supp_instructions= "" if i >= len(NAVIGATION_LVL_6) else NAVIGATION_LVL_6[i])
                i += 1
                action = self.get_navigation_action(image_urls, message, mode=self.action_mode)
                
            if action == 'stop': 
                print("Action stop is chosen")
                break
            elif action == 'lost':
                self.help_message = self.ask_for_help(mode=self.action_mode)
            else:
                err_message = self.step(action)
                if err_message != '':  # if has err, pass err message as help message
                    self.help_message = err_message
                                    
            if self.show_info: 
                print(self.show_state_info(self.graph_state))
    
class Oracle: 
    def __init__(self, oracle_config: dict): 
        oracle_agent_prompt = oracle_config["prompt"]
        llm_config = {"config_list": [{"model": "gpt-4o-mini", "api_key": os.environ.get("OPENAI_API_KEY")}]}
        self.mode = oracle_config["mode"]
        self.question = oracle_config["question"]
        # self.mode = "human"
        #TODO create a new openAI agent here  
    def get_answer(self, question): 
        #TODO get answer from the model 
        if self.mode == "human": 
            print(f"Question: {question}")
            answer = input("Enter the answer: ")
        return answer
        
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

    #navi_config = r"config\human_test_navi.json"
    navi_config = os.path.join("config", "openai_test_navi_3.json")
    # navi_config = r"config\poe_test_navi.json"
    oracle_config = os.path.join("config", "human_test_oracle.json")
    vision_config = r"config\human_test_vision.json"

    navigator = Navigator(config=navi_config, oracle_config=oracle_config, answering_config=vision_config, show_info=False)
    # show_graph_info(navigator.graph)
    image_features = navigator.get_image_feature(graph_state=('65287201', 0), mode="poe_send_message")
    print(image_features)
    test = navigator.get_navigation_action(image_urls=image_features, message="Where are we")
    print(test)