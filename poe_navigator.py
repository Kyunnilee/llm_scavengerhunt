from base_navigator import BaseNavigator
from poe_api_wrapper import PoeApi
import json
from map import get_street_view_image_url
import os 

api_key = os.get_env('GOOGLE_MAP_API_KEY')

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
        if config: 
           self.config = json.loads(config)

        if oracle_config: 
            self.oracle.config = json.loads(config)

        self.tokens = self.config['tokens']
        self.model = config['model']
        self.client = PoeApi(tokens=self.tokens)
        system_prompt = config['policy']
        chunk = self.send_message(system_prompt)
        self.chat_id = chunk['chatId'] #to get continue the conversation in the same thread 

        self.oracle = Oracle(oracle_config)

    def send_message(self, message: str, files: str = None, chat_id: str = None, graph_state = None):
        '''
        may need to change along if we are doing it the base64 encoding case 
        ''' 
        for chunk in self.client.send_message(bot=self.model, message=message, file_path=[files], chatId=chat_id): 
            pass 
        return chunk 
        
    def get_navigation_instructions(self, image_features: str, graph_state):
        panoid, heading = graph_state 
        lat, lon = self.graph.nodes[panoid].coordinate

        message = f"You are currently at {lat}, {lon} facing {heading}. Where should I go next?"
        chunk = self.send_message(message=message, files=image_features, chat_id=self.chat_id) 
        move = chunk["text"]["move"]
        if move == 'LOST':
            self.ask_for_help(chunk['directions'], graph_state)
        return move 
    
    def get_image_feature(self, graph_state): 
        panoid, heading = graph_state
        lat, lon = self.graph.nodes[panoid].coordinate
        image_url = get_street_view_image_url(lat, lon, api_key, heading)
        return image_url, graph_state
        '''
        doc mentioned that this was necessary to align the heading of the panorama with the actual heading of the image but if we using url then ?? 
        # shift_angle = 157.5 + self.graph.nodes[panoid].pano_yaw_angle - heading 
        # width = image_feature.shape[1]
        # shift = int(width * shift_angle / 360)
        # image_feature = np.roll(image_feature, shift, axis=1)
        # return image_feature
        '''
    
    def ask_for_help(self, reply_from_llm, graph_state): 
        '''
        ask oracle when necessary ? 
        TODO -> read human input should be able to work / gpt4o model for  
        '''

    def forward(self, start_graph_state, show_info): 
        self.graph_state = start_graph_state

        while True: 
            image_url, self.graph_state = self.get_image_feature(self.graph_state)
            move = self.get_navigation_instructions(image_url, self.graph_state)
            if move == 'stop': 
                print("Action stop is chosen")
                break 
            self.step(move)

            if show_info: 
                self.show_state_info(self.graph_state) 
    
class Oracle: 
    def __init__(self, oracle_config): 
        oracle_agent_prompt = oracle_config["prompt"]
        llm_config = {"config_list": [{"model": "gpt-4o-mini", "api_key": os.environ.get("OPENAI_API_KEY")}]}
        
        #TODO create a new openAI agent here  
        

    

if __name__ == "__main__":   
    navigator = Navigator()
    navigator.forward(
        start_graph_state=('ChIJo0BPGZl-hYARkgJpLsjrtY4', 209), 
        show_info=True
    )
