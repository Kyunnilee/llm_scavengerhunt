
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
        self.messages_history = []
    
    def send_message(self, message:str, image_urls=[]):
        image_parts = []
        for url in image_urls:
            image = load_image_from_url(url)
            image_parts.append(image)
        
        response = self.chat.send_message([message]+image_parts)
        self.messages_history.append({"role": "user", "parts": message})
        self.messages_history.append({"role": "model", "parts": response.text})
        self.chat = self.model.start_chat(history=self.messages_history)
        return response.text

if __name__ == "__main__":
    # test
    cfg = {
        "model": "gemini-1.5-flash",
        "policy": "**Role Instructions**: You are a navigation agent participating in a scavenger hunt game. Your objective is to locate a designated destination as efficiently as possible using the information provided at each step. Analyze visual and positional data carefully, decide on strategic actions to move closer to the goal, and only when necessary, ask questions to gather additional information.\n---\n**Task Rules**:\n1. **Input Information**: At each step, you will receive the following:\n   - **Current Position**: Your current location described textually.\n   - **Current Heading**: A number between -180 and 180 indicating the direction you are facing (0 = North, 90 = East, 180 = South, -90 = West).\n   - **Visual Information**: Five street view images corresponding to your surroundings:\n     - **Left**: 90 degrees counter-clockwise from your heading.\n     - **Left-forward**: 45 degrees counter-clockwise from your heading.\n     - **Front**: Aligned with your heading.\n     - **Right-forward**: 45 degrees clockwise from your heading.\n     - **Right**: 90 degrees clockwise from your heading.\n2. **Available Actions**:\n   - **forward**: Move one step forward to a new position.\n   - **left**/**right**/**turn_around**: Change your heading at the current position.\n   - **ask**: Indicate that you need additional information about the destination or environment.\n     **Note**: When you choose **ask**, you do not need to formulate a specific question immediately. Instead, this action signals your intent to gather information, and the system will provide an opportunity in the next step to clarify and specify the question.\n   - **stop**: Indicate that you have reached the destination or its vicinity.\n3. **Action-Specific Guidance**:\n   - If your action is **ask**, your current response should include only the decision `[Action: ask]` without crafting the specific question.\n   - The system will return a prompt in the next round for you to organize your question based on updated context and observations. This ensures your question is targeted and relevant.\n4. **Success Condition**: The task is considered successful if you choose **stop** when the destination is nearby.\n---\n**Strategy**:\n- Analyze the provided positional and visual data thoroughly before making any decision.\n- If unsure about the destination's location, use **ask** to gather essential information but focus on asking only when necessary to avoid redundant or irrelevant inquiries.\n- Prioritize efficient movements and strategic questioning to achieve the goal with minimal steps.\n---\n**Output Format**:\n1. **Analysis**: Summarize key observations (e.g., visible landmarks, directional clues, or features relevant to the target).\n2. **Reasoning**: Briefly explain the logic behind your chosen action.\n3. **Decision**: Format your action as `[Action: forward/left/right/turn_around/ask/stop]`, e.g., `[Action: ask]`.\n---\n**Current Target**: <<<target_name>>>"
    }
    agent = GeminiAgent(cfg)
    response = agent.send_message('''You are currently at 40.746652, -73.990055 facing -142.The five images below show the view in different directions, they are on your left, front-left, front, front-right, and right.
You can take following action, only these actions are available in this position: 
[Action: forward], go to: (40.746566, -73.99012), heading: -143
[Action: turn_around], heading: 34
[Action: ask], ask for help.
[Action: stop], report arrival.

describe the images above first.''', 
                                  image_urls=[
            "https://maps.googleapis.com/maps/api/streetview?size=450x450&location=40.746652,-73.990055&key=AIzaSyBZdkQTQnrPBtfpmlPh5-Ngs5vdMO2Xy80&fov=90&heading=128&pitch=0&source=outdoor",
            "https://maps.googleapis.com/maps/api/streetview?size=450x450&location=40.746652,-73.990055&key=AIzaSyBZdkQTQnrPBtfpmlPh5-Ngs5vdMO2Xy80&fov=90&heading=173&pitch=0&source=outdoor",
            "https://maps.googleapis.com/maps/api/streetview?size=450x450&location=40.746652,-73.990055&key=AIzaSyBZdkQTQnrPBtfpmlPh5-Ngs5vdMO2Xy80&fov=90&heading=218&pitch=0&source=outdoor",
            "https://maps.googleapis.com/maps/api/streetview?size=450x450&location=40.746652,-73.990055&key=AIzaSyBZdkQTQnrPBtfpmlPh5-Ngs5vdMO2Xy80&fov=90&heading=263&pitch=0&source=outdoor",
            "https://maps.googleapis.com/maps/api/streetview?size=450x450&location=40.746652,-73.990055&key=AIzaSyBZdkQTQnrPBtfpmlPh5-Ngs5vdMO2Xy80&fov=90&heading=308&pitch=0&source=outdoor"
        ])
    print(response)
    
    response2 = agent.send_message("how do you like the images? how many images are there?",)
    print(response2)
    
    print('\n\n')
    for his in agent.chat.history:
        print(his)
        print('---')
    
