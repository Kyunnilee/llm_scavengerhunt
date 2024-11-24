from poe_api_wrapper import PoeApi
import time
tokens = {
        'p-b': ..., 
        'p-lat': ..., 
        'formkey': ...,
        '__cf_bm': '...',
        'cf_clearance': ...,
    } 
class PoeAgent():
    def __init__(self, cfg):
        self.tokens = cfg['tokens']
        self.model = cfg['model']
        self.client = PoeApi(tokens=self.tokens)
        system_prompt = cfg['policy']
        self.chat_id = None
        chunk = self.send_message(system_prompt)
        self.chat_id = chunk['chatId'] #to get continue the conversation in the same thread 
        
    def send_message(self, message:str, image_paths=[]):
        '''
        may need to change along if we are doing it the base64 encoding case 
        TODO: not stable yet!!
        ''' 
        for chunk in self.client.send_message(bot=self.model, message=message, file_path=image_paths, chatId=self.chat_id): 
            time.sleep(0.01)
            pass 
        return chunk 