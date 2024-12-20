import os
import json

def get_agent_response(log_info:dict):
        qa_messages = log_info.get("qa_messages")
        question_answer = ""
        if qa_messages:
            question_answer += "Question and answer with oracle: "
            for q, a in zip(qa_messages["question"], qa_messages["answer"]):
                question_answer += f"Agent: {q}\nOracle: {a}\n\n"
        
        message = log_info["message"][0] + question_answer
        action = log_info["action"]
        action_message = log_info["action_message"]
        agent_response = ("Context: " + message, "Agent Action: " + action, "Agent Response: " + action_message)
        return agent_response
        

log_root = r'output\logs'
qa_data = []
agent_response = []

for root, _, files in os.walk(log_root):
    for file in files:
        if file.endswith('.json'):
            path = os.path.join(root, file)
            with open(path, 'r') as f:
                data = json.load(f)
            for info in data:
                if "qa_messages" in info:
                    qa_data.append(info["qa_messages"])
                    agent_response.append(get_agent_response(info))

    
with open("tmp/agent_response_exaples.json", "w") as f:
    json.dump(agent_response, f, indent=4)
    
with open("tmp/qa_data.json", "w") as f:
    json.dump(qa_data, f, indent=4)

print(f"Num of QA data: {len(qa_data)}")