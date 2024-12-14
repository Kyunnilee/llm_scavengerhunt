import anthropic
import requests
import base64

def image_url_to_base64(image_url: str) -> str:
    response = requests.get(image_url)
    if response.status_code == 200:
        image_data = response.content
        base64_encoded = base64.b64encode(image_data).decode('utf-8')
        return base64_encoded
    else:
        raise Exception(f"Failed to turn image into base64, status code: {response.status_code}")
    

def del_images(message):
    content = message['content']
    new_content = []
    for c in content:
        if c['type'] != 'image':
            new_content.append(c)
    message['content'] = new_content
    return message
    
class AnthropicAgent:
    def __init__(self, cfg):
        self.client = anthropic.Anthropic()
        self.messages = []
        self.model = cfg['model']
        self.policy = cfg['policy']
        
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
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": image_url_to_base64(url)
                    }
                })
        
        message_feed = self.messages.copy()
        message_feed.append(new_message)        
        
        response = self.client.messages.create(
            system=self.policy,
            model=self.model,
            messages=message_feed,
            max_tokens=1024
        )
        
        self.messages.append(del_images(new_message))
        
        reply_content = response.content[0].text
        self.messages.append({
            "role": "assistant",
            "content": reply_content
        })
        
        return reply_content
    
if __name__ == "__main__":
    # test
    agent = AnthropicAgent({
        "model": "claude-3-5-sonnet-20241022",
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