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
                
        self.messages.append(new_message)
        
        message = self.client.messages.create(
            system=self.policy,
            model=self.model,
            messages=self.messages,
            max_tokens=1024
        )
        
        reply_content = message.content[0].text
        self.messages.append({
            "role": "assistant",
            "content": reply_content
        })
        
        return reply_content
    
if __name__ == "__main__":
    # test
    anthropic_agent = AnthropicAgent({
        "model": "claude-3-5-sonnet-20241022",
        "policy": "You are a world-class poet. Respond only with short poems."
    })
    
    reply = anthropic_agent.send_message("What's in this image?", ["https://maps.googleapis.com/maps/api/streetview?size=300x300&location=37.869545,-122.2527&key=AIzaSyBZdkQTQnrPBtfpmlPh5-Ngs5vdMO2Xy80&fov=90&heading=0&pitch=0&source=outdoor", "https://maps.googleapis.com/maps/api/streetview?size=300x300&location=37.868577,-122.2527&key=AIzaSyBZdkQTQnrPBtfpmlPh5-Ngs5vdMO2Xy80&fov=90&heading=0&pitch=0&source=outdoor"])
    print(reply)
    
    reply2 = anthropic_agent.send_message("what if a cute cat appear in the center of the image")
    print(reply2)