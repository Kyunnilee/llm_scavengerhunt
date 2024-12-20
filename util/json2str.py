import json
def calculate_score_with_json(log_info:list[dict]):
        shortest_step = log_info[1]["shortest_path"]
        agent_response = []
        for i in range(1, len(log_info)):
            qa_messages = log_info[i].get("qa_messages")
            question_answer = ""
            if qa_messages:
                question_answer += "Question and answer with oracle: "
                for q, a in zip(qa_messages["question"], qa_messages["answer"]):
                    question_answer += f"Agent: {q}\nOracle: {a}\n\n"
            
            message = log_info[i]["message"][0] + question_answer
            action = log_info[i]["action"]
            action_message = log_info[i]["action_message"]
            agent_response.append(("Context: " + message, "Agent Action: " + action, "Agent Response: " + action_message))

        return str(agent_response)

with open("notable_outputs\log_infos_10.json", "r") as file:
        data = json.load(file)
    # print(type(data))
print(repr(calculate_score_with_json(data)))
    