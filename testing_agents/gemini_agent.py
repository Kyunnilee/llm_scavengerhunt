
import google.generativeai as genai
import requests
from PIL import Image
from io import BytesIO

def load_image_from_url(url: str) -> Image.Image:
    response = requests.get(url)
    if response.status_code == 200:
        image_data = BytesIO(response.content)
        image = Image.open(image_data)
        return image
    else:
        raise Exception(f"Failed to download image, status code: {response.status_code}")

class GeminiAgent:
    def __init__(self, cfg):
        self.model = genai.GenerativeModel(model_name=cfg['model'],
                                           system_instruction=cfg['policy'])
        self.chat = self.model.start_chat(history=[])
    
    def send_message(self, message:str, image_urls=[]):
        image_parts = []
        for url in image_urls:
            image = load_image_from_url(url)
            image_parts.append(image)
        
        response = self.chat.send_message([message, *image_parts])
        return response.text

if __name__ == "__main__":
    # test
    cfg = {
        "model": "gemini-1.5-flash-002",
        "policy": "You are a helpful assistant."
    }
    agent = GeminiAgent(cfg)
    response = agent.send_message("What's in this image?", 
                                  image_urls=["https://maps.googleapis.com/maps/api/streetview?size=300x300&location=37.869545,-122.2527&key=AIzaSyBZdkQTQnrPBtfpmlPh5-Ngs5vdMO2Xy80&fov=90&heading=0&pitch=0&source=outdoor",
                                              "https://maps.googleapis.com/maps/api/streetview?size=300x300&location=37.868577,-122.2527&key=AIzaSyBZdkQTQnrPBtfpmlPh5-Ngs5vdMO2Xy80&fov=90&heading=0&pitch=0&source=outdoor"])
    print(response)
    
    
    response2 = agent.send_message("how do you like the images? how many images are there?",)
    print(response2)
