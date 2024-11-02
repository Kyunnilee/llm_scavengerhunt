from openai import OpenAI
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
        
        self.messages.append(new_message)
        
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
        )
        
        reply_content = completion.choices[0].message.content
        self.messages.append({
            "role": "assistant",
            "content": reply_content
        })
        
        return reply_content
        
        

if __name__ == "__main__":
    # test
    client = OpenAI()

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What's in this image?"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "https://maps.googleapis.com/maps/api/streetview?size=300x300&location=37.869545,-122.2527&key=AIzaSyBZdkQTQnrPBtfpmlPh5-Ngs5vdMO2Xy80&fov=90&heading=0&pitch=0&source=outdoor",
                        }
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "https://maps.googleapis.com/maps/api/streetview?size=300x300&location=37.868577,-122.2527&key=AIzaSyBZdkQTQnrPBtfpmlPh5-Ngs5vdMO2Xy80&fov=90&heading=0&pitch=0&source=outdoor",
                        }
                    }
                ],
            }
        ],
    )

    print(completion.choices[0].message.content)