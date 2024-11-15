from openai import OpenAI
import os 

api_key=os.environ.get("OPENAI_API_KEY")

class VisionAnswering: 
    def __init__(self, config): 
        self.client = OpenAI(api_key=api_key)
        self.base_system_prompt = config['system_prompt']
        self.image_system = config['image_system']
        self.model = config['model']
    
    def get_image_summary(self, image_path, is_debug): 
        content =[
            {"type": "text", "text": self.image_system}, 
            {
                "type": "image_url",
                "image_url": {
                    "url": image_path
                }
            } 
        ]
        full_message = [
            {"role": "system", "content": self.base_system_prompt},
            {"role": "user", "content": content}
        ]
        response = self.client.chat.completions.create(
            model=self.model,
            messages=full_message,
            max_tokens=300
        )

        output = response.choices[0]
        if is_debug: 
            print(output)
        resp =  response.choices[0].message.content
        return resp

    def order_image_summaries(self, offsets, image_paths, is_debug): 
        op = {}
        for i in range(len(image_paths)): 
            resp = self.get_image_summary(image_paths[i], is_debug)
            op[offsets[i]] = resp    
        return op 

if __name__=="__main__": 
    test_prompt = """You are a helpful assistant replying to image queries, observing key details within the picture with the aim to identify exactly where you are"""
    test_config = {
        'system_prompt': test_prompt, 
        'model': 'gpt-4o-mini' 
    }
    answerer = VisionAnswering(test_config)
    print(answerer)
    resp = answerer.get_image_summary("https://maps.googleapis.com/maps/api/streetview?size=300x300&location=37.869545,-122.2527&key=AIzaSyDv1zr5JJYKjv3MGIeYNEe5n1nP4gv2SSY&fov=90&heading=0&pitch=0&source=outdoor", True)
    print(resp)