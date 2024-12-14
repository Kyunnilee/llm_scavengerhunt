import os
from mistralai import Mistral

api_key = "m7CP2GV4U2uTWoDoWK612otgjVh5Hct5"
def del_images(message):
    content = message['content']
    new_content = []
    for c in content:
        if c['type'] != 'image_url':
            new_content.append(c)
    message['content'] = new_content
    return message
class MistralaiAgent:
    def __init__(self, cfg):
        self.client = Mistral(api_key=api_key)
        self.messages = [{
            "role": "system",
            "content": [{
                "type": "text",
                "text": cfg['policy']
            }]
        }]
        self.model = cfg['model']
        
    def send_message(self, message:str, image_urls=[]):
        new_message = {
            "role": "user",
            "content": [
                {"type": "text", "text": message},
            ]
        }
        
        if len(image_urls) > 0:
            for url in image_urls:
                new_message['content'].append({
                    "type": "image_url",
                    "image_url": url
                })
        
        message_feed = self.messages.copy()
        message_feed.append(new_message)
        
        completion = self.client.chat.complete(
            model=self.model,
            messages=message_feed,
        )
        
        self.messages.append(del_images(new_message))
        
        reply_content = completion.choices[0].message.content
        self.messages.append({
            "role": "assistant",
            "content": reply_content
        })
        
        return reply_content
    
    
if __name__ == "__main__":
    # test
    mistralai_agent = MistralaiAgent({
        "model": "pixtral-12b-2409",
        "policy": "You are a helpful assistant."
    })
    
    response = mistralai_agent.send_message("What's in images? What's the difference", 
                                  image_urls=["https://maps.googleapis.com/maps/api/streetview?size=300x300&location=37.869545,-122.2527&key=AIzaSyBZdkQTQnrPBtfpmlPh5-Ngs5vdMO2Xy80&fov=90&heading=0&pitch=0&source=outdoor",
                                              "https://maps.googleapis.com/maps/api/streetview?size=300x300&location=37.868577,-122.2527&key=AIzaSyBZdkQTQnrPBtfpmlPh5-Ngs5vdMO2Xy80&fov=90&heading=0&pitch=0&source=outdoor"])
    print(response)
    
    
    response2 = mistralai_agent.send_message("how do you like the images? how many images are there?",)
    print(response2)