from openai import OpenAI

def del_images(message):
    content = message['content']
    new_content = []
    for c in content:
        if c['type'] != 'image_url':
            new_content.append(c)
    message['content'] = new_content
    return message

class OpenAIAgent:
    def __init__(self, cfg):
        self.client = OpenAI()
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
                    "image_url": {
                        "url": url
                    }
                })
        
        message_feed = self.messages.copy()
        message_feed.append(new_message)
        
        completion = self.client.chat.completions.create(
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
    agent = OpenAIAgent({
        "model": "gpt-4o-mini",
        "policy": "You are a helpful assistant."
    })
    
    reply = agent.send_message("What's in this image?", ["https://maps.googleapis.com/maps/api/streetview?size=300x300&location=37.869545,-122.2527&key=AIzaSyBZdkQTQnrPBtfpmlPh5-Ngs5vdMO2Xy80&fov=90&heading=0&pitch=0&source=outdoor", "https://maps.googleapis.com/maps/api/streetview?size=300x300&location=37.868577,-122.2527&key=AIzaSyBZdkQTQnrPBtfpmlPh5-Ngs5vdMO2Xy80&fov=90&heading=0&pitch=0&source=outdoor"])
    print(reply)
    
    reply2 = agent.send_message("what if a cute cat appear in the center of the image")
    print(reply2)
    print(agent.messages)   
    
    reply3 = agent.send_message("tell difference in images, compare to previous image", [
            "https://maps.googleapis.com/maps/api/streetview?size=300x300&location=40.746652,-73.990055&key=AIzaSyBZdkQTQnrPBtfpmlPh5-Ngs5vdMO2Xy80&fov=90&heading=304&pitch=0&source=outdoor",
            "https://maps.googleapis.com/maps/api/streetview?size=300x300&location=40.746652,-73.990055&key=AIzaSyBZdkQTQnrPBtfpmlPh5-Ngs5vdMO2Xy80&fov=90&heading=349&pitch=0&source=outdoor",
            "https://maps.googleapis.com/maps/api/streetview?size=300x300&location=40.746652,-73.990055&key=AIzaSyBZdkQTQnrPBtfpmlPh5-Ngs5vdMO2Xy80&fov=90&heading=34&pitch=0&source=outdoor",
            "https://maps.googleapis.com/maps/api/streetview?size=300x300&location=40.746652,-73.990055&key=AIzaSyBZdkQTQnrPBtfpmlPh5-Ngs5vdMO2Xy80&fov=90&heading=79&pitch=0&source=outdoor",
            "https://maps.googleapis.com/maps/api/streetview?size=300x300&location=40.746652,-73.990055&key=AIzaSyBZdkQTQnrPBtfpmlPh5-Ngs5vdMO2Xy80&fov=90&heading=124&pitch=0&source=outdoor"
        ])
    print(reply3)
    print(agent.messages)
    
    