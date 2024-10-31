from base_navigator import BaseNavigator
from poe_api_wrapper import PoeApi
import json
from map import get_street_view_image_url
import os 

api_key = os.getenv('GOOGLE_MAP_API_KEY')

class Navigator(BaseNavigator):
    tokens = {
        'p-b': ..., 
        'p-lat': ..., 
        'formkey': ...,
        '__cf_bm': '...',
        'cf_clearance': ...,
    } 

    def __init__(self, config=None, oracle_config=None): 
        super().__init__()
        # if config: 
        #     with open(config, 'r') as f:
        #         self.config = json.loads(f)

        # if oracle_config: 
        #     with open(oracle_config, 'r') as f:
        #         self.oracle.config = json.load(f)
        # control_mode = self.config['mode']
        control_mode = "human"
    

        if control_mode == "poe":
            self.tokens = self.config['tokens']
            self.model = config['model']
            self.client = PoeApi(tokens=self.tokens)
            self.action_mode = "poe_send_message"
        elif control_mode == "human":
            self.action_mode = "human"
        
        # system_prompt = config['policy']
        # chunk = self.send_message(system_prompt)
        # self.chat_id = chunk['chatId'] #to get continue the conversation in the same thread 

        self.oracle = Oracle(oracle_config)

    def send_message(self, message: str, files: str = None, chat_id: str = None, graph_state = None):
        '''
        may need to change along if we are doing it the base64 encoding case 
        ''' 
        for chunk in self.client.send_message(bot=self.model, message=message, file_path=[files], chatId=chat_id): 
            pass 
        return chunk 
        
    def get_navigation_instructions(self, help_message=None, phase="new_state"): #phase = new_state, help
        if phase == "new_state":
            panoid, heading = self.graph_state 
            lat, lon = self.graph.get_node_coordinates(panoid)
            message = f"You are currently at {lat}, {lon} facing {heading}."
            message += "The five images below show the view in different directions, they are on your left, front-left, front, front-right, and right."
            # message2 = "You can go through the following directions, to the new nodes: " + self.get_state_edges(self.graph_state)
            message3 = "You can take following action: " + self.show_state_info(self.graph_state)
            message += message3
        elif phase == "help":
            message = help_message
        return message
    
    def get_navigation_action(self, image_features: str, message: str, mode="poe_send_message"):
        print("="*50)
        print("Getting navigation action")
        print(f"Message: {message}")
        print(f"Image features: {image_features}")
        print("="*50)
        
        if mode == "poe_send_message":
            chunk = self.send_message(message=message, files=image_features, chat_id=self.chat_id)
            move = chunk["text"]["move"]
        elif mode == "human":
            move = input("Enter the move: ")
        return move
    
    def get_image_feature(self, graph_state): 
        panoid, heading = graph_state
        lat, lon = self.graph.nodes[panoid].coordinate

        image_urls = []
        for offset in [-90, -45, 0, 45, 90]:
            heading_image = (heading + offset) % 360
            image_url = get_street_view_image_url(lat, lon, api_key, heading_image)
            image_urls.append(image_url)
        return image_urls
        '''
        doc mentioned that this was necessary to align the heading of the panorama with the actual heading of the image but if we using url then ?? 
        # shift_angle = 157.5 + self.graph.nodes[panoid].pano_yaw_angle - heading 
        # width = image_feature.shape[1]
        # shift = int(width * shift_angle / 360)
        # image_feature = np.roll(image_feature, shift, axis=1)
        # return image_feature
        '''

    def ask_for_help(self, mode="human"): 
        '''
        return answer from the oracle
        TODO -> read human input should be able to work / gpt4o model for  
        '''
        message = "What do you want to ask about ?"
        if mode == "poe_send_message":
            chunk = self.send_message(message=message, chat_id=self.chat_id)
            question = chunk['text']
        elif mode == "human":
            question = input("Enter the question: ")
       
        help_message = self.oracle.get_answer(question)
        return help_message

    def forward(self, start_graph_state, show_info): 
        self.graph_state = start_graph_state
        self.graph_state = self.fix_heading(self.graph_state)
        print(f"Heading {start_graph_state[1]} -> {self.graph_state[1]}")
        self.help_message = None

        while True: 
            # get action/move
            if self.help_message: # is asking for help
                message = self.get_navigation_instructions(self.help_message, phase="help")
                move = self.get_navigation_action(None, message, mode=self.action_mode)
                self.help_message = None
            else:
                image_urls = self.get_image_feature(self.graph_state)
                message = self.get_navigation_instructions()
                move = self.get_navigation_action(image_urls, message, mode=self.action_mode)
                
            if move == 'stop': 
                print("Action stop is chosen")
                break
            elif move == 'LOST':
                self.help_message = self.ask_for_help(mode=self.action_mode)
            else:
                self.step(move)
                
            if show_info: 
                self.show_state_info(self.graph_state) 
    
class Oracle: 
    def __init__(self, oracle_config): 
        # oracle_agent_prompt = oracle_config["prompt"]
        # llm_config = {"config_list": [{"model": "gpt-4o-mini", "api_key": os.environ.get("OPENAI_API_KEY")}]}
        # self.mode = oracle_config["mode"]
        self.mode = "human"
        #TODO create a new openAI agent here  
    def get_answer(self, question): 
        #TODO get answer from the model 
        if self.mode == "human": 
            print(f"Question: {question}")
            answer = input("Enter the answer: ")
        return answer
        
if __name__ == "__main__":   
    navi_config = r"config\human_test_navi.json"
    oracle_config = r"config\human_test_oracle.json"
    
    navigator = Navigator(config=navi_config, oracle_config=oracle_config)
    navigator.forward(
        start_graph_state=('HgFMRzAguxKiBHkwCQ_TgQ', 0), 
        show_info=True
    )
