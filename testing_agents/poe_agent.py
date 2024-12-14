from poe_api_wrapper import PoeApi
import time
import requests
import tempfile
import os
tokens = {
        'p-b': ..., 
        'p-lat': ..., 
        'formkey': ...,
        '__cf_bm': '...',
        'cf_clearance': ...,
    } 

system_prompt_template = "Your current message context:\n <System> <<<content>>> </System>"

class PoeAgent():
    def __init__(self, cfg):
        self.tokens = cfg['tokens']
        self.model = cfg['model']
        self.client = PoeApi(tokens=self.tokens)
        self.system_prompt = cfg['policy']
        self.chat_id = None
        chunk = self._send_message_chunk(self.system_prompt)
        self.chat_id = chunk['chatId'] #to get continue the conversation in the same thread 
        
    def _send_message_chunk(self, message:str, image_paths=[]):
        '''
        may need to change along if we are doing it the base64 encoding case 
        TODO: not stable yet!!
        ''' 
        for chunk in self.client.send_message(bot=self.model, message=message, file_path=image_paths, chatId=self.chat_id): 
            time.sleep(0.01)
            pass 
        return chunk
    
    def send_message(self, message:str, image_urls=[]):
        image_feed = []
        temp_dir = tempfile.mkdtemp()
        message_feed = system_prompt_template.replace("<<<content>>>", self.system_prompt) + "\n" + message
        try:
            for i, image_url in enumerate(image_urls):
                response = requests.get(image_url)
                if response.status_code == 200:
                    temp_file_path = os.path.join(temp_dir, f"{i}.jpg")
                    with open(temp_file_path, 'wb') as f:
                        f.write(response.content)
                    image_feed.append(temp_file_path)
                else:
                    print(f"Failed to download image from {image_url}")
            for chunk in self.client.send_message(bot=self.model, message=message_feed, file_path=image_feed, chatId=self.chat_id):
                time.sleep(0.01)
                pass
            return chunk['text']
        finally:
            for temp_file_path in image_feed:
                os.remove(temp_file_path)
            os.rmdir(temp_dir)
    
if __name__ == "__main__":
    cfg = {
    "mode": "poe",
    "model": "gpt4_o_mini_128k",
    "tokens" : {
        "p-b": "aXIj0yshxMVZe5EQrj-Xqw%3D%3D",
        "p-lat": "SPKVAm2Ep57juUJo5%2Bb%2FW1RhwSyiLYGakXqaOwpd8A%3D%3D",
        "formkey": "f6e323b2f1d43ecd5834b7f43627ecc5",
        "__cf_bm": "j6TQopuSTecEBdkGzH6CpyHPsaiy8ug9l8rNbhRe_DA-1730408522-1.0.1.1-BbFwbHVuUippDE9dr81I3TLp17w81yy2z.qgzkOXD_Lct_mpAHRmmktdS6nZGFwdF9M8phzt3fZUeN43inZg7w",
        "cf_clearance": "4Kjd1IlcvAOSA3uqHekE1.oODj7h.kQn7IDz0pQMJGI-1730406185-1.2.1.1-n7E25aq.oovFIhsdahgfJjx9Ce5VRtOIgSJkw.Vu.aBTNEZmiuNDZlfknQae1lFWLz06aETDbHILsAZ43ue446C6EKCJLYkX0bgzEUj5Xi39qApomRR.W1WL8Q4ttUA6Xg6Z9PPaH0nKXtSLWq8RanHdiYp7pm4qwxEDFIghKxV1qMxFl_X5PwVYopJFVvQgHclBBWWSzDVqpyCPKPumMe8GrsEgYT9zqZJVRB47msiIVMKUZVYINwRSygRiHsKTdvbpZLVJkUxV4gKIE0esLTCzNG6FQySXJ4aVLSGRswzUdR0yByX69tou6dbVXdjX8vsTUWgZhvUQqdo__xjTQGN7byyX3y9mjhFr9Q3f0Uyypch1UUm51QCZAVdlBG3Zq7UiN6BYiUyJkmJ7Bga3wA"
    },
    "policy": "You are a person who is on a scavenger hunt in the city and you need to find the [<<<target_name>>>]. Whenever you arrive at a new location, I will show you some images of the street around you, and tell you where you are and where you are heading. After thinking about it, you need to give your actions. Your possible actions are as follows: [forward, left, right, turn_around, stop, ask]. Select forward to get to the next point where you are currently facing, and select left/right, where you will change orientation. When you don't know how to act, you can choose the action `ask`, and then I will ask you what is the point of confusion, in the rest of the conversation, you need to ask questions to help you obtain information to decide on the action. Finally, if you think you have reached your destination, use Action stop. You should give action at end of your reply, the formulation should be like: [Action: YOU ACTION]. You should figure out how to go to the <<<target_name>>> before you move",
    "vision_mode": "url"
    }
    agent = PoeAgent(cfg)
    reply = agent.send_message("what do you see in the images below?",image_urls=[
            "https://maps.googleapis.com/maps/api/streetview?size=300x300&location=40.746652,-73.990055&key=AIzaSyBZdkQTQnrPBtfpmlPh5-Ngs5vdMO2Xy80&fov=90&heading=304&pitch=0&source=outdoor",
            "https://maps.googleapis.com/maps/api/streetview?size=300x300&location=40.746652,-73.990055&key=AIzaSyBZdkQTQnrPBtfpmlPh5-Ngs5vdMO2Xy80&fov=90&heading=349&pitch=0&source=outdoor",
            "https://maps.googleapis.com/maps/api/streetview?size=300x300&location=40.746652,-73.990055&key=AIzaSyBZdkQTQnrPBtfpmlPh5-Ngs5vdMO2Xy80&fov=90&heading=34&pitch=0&source=outdoor",
            "https://maps.googleapis.com/maps/api/streetview?size=300x300&location=40.746652,-73.990055&key=AIzaSyBZdkQTQnrPBtfpmlPh5-Ngs5vdMO2Xy80&fov=90&heading=79&pitch=0&source=outdoor",
            "https://maps.googleapis.com/maps/api/streetview?size=300x300&location=40.746652,-73.990055&key=AIzaSyBZdkQTQnrPBtfpmlPh5-Ngs5vdMO2Xy80&fov=90&heading=124&pitch=0&source=outdoor"
        ])
    print(reply)