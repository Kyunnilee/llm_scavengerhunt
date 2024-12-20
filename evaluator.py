# -*- coding:utf-8 -*-

from graph_loader import GraphLoader, haversine
from openai import OpenAI
from util.json2str import json2str
from tqdm import tqdm

import os
import json
import ast
import re

api_key=os.environ.get("OPENAI_API_KEY")

def extract_scores(text: str):
    score_pattern = r"\[evaluated_sc_begin\](.*?)\[evaluated_sc_end\]"
    score_justification_pattern = r"\[evaluated_sc_justification_begin\](.*?)\[evaluated_sc_justification_end\]"

    action_score_pattern = r"\[action_reasoning_score\](.*?)\[action_reasoning_score_end\]"
    action_justification_pattern = r"\[action_reasoning_score_justification\](.*?)\[action_reasoning_score_justification_end\]"
    
    question_score_pattern = r"\[question_score\](.*?)\[question_score_end\]"
    question_justification_pattern = r"\[question_score_justification\](.*?)\[question_score_justification_end\]"

    score = re.search(score_pattern, text, re.DOTALL | re.MULTILINE)

    if score:
        score = score.group(1).strip()
        print(score)
    else:   
        score = text 
    score_justification = re.search(score_justification_pattern, text, re.DOTALL | re.MULTILINE)
    if score_justification:
        score_justification = score_justification.group(1).strip()
    else:
        score_justification = text
    return (score, score_justification)

    # action_score = re.search(action_score_pattern, text)
    # if action_score:
    #     action_score = action_score.group(1).strip()
    # else:
    #     action_score = text
    
    # action_justification = re.search(action_justification_pattern, text)
    # if action_justification:
    #     action_justification = action_justification.group(1).strip()
    # else:
    #     action_justification = text
        
    # question_score = re.search(question_score_pattern, text)
    # if question_score:
    #     question_score = question_score.group(1).strip()
    # else:
    #     question_score = text
        
    # question_justification = re.search(question_justification_pattern, text)
    # if question_justification:
    #     question_justification = question_justification.group(1).strip()
    # else:
    #     question_justification = text
        
    # return (action_score, action_justification), (question_score, question_justification)
    
class AgentEvaluator:
    def __init__(self, config): 
        self.client = OpenAI(api_key=api_key)
        self.base_system_prompt = config['system_prompt']
        self.model = config['model']

    def evaluate_misc(self, total_response, shortest_step, num_steps, num_q):
        '''
        Evaluate the number of questions asked (int), number of steps took to reach destination (int), and whether the agent finished (bool)

        total_response: List of pairs in the following format [("Context: " + message, "Agent Action: " + action)]/ One node, one action
        '''
        # total_response = list of "Context message and action message string" 
        # num_steps = 0 # num of Forwards
        # eval_num_questions, eval_num_steps = 0, 0 # evaluated benchmark value of # questions and 3 steps taken
        # #eval_finished = current_pos == target_pos # evaluated benchmark value whether the agent reached the goal or not

        # num_steps = len([pair for pair in total_response if "forward" in pair[1]])
        # if num_steps == 0:  
        #     num_steps = 1
        eval_num_questions = len([pair for pair in total_response if "ask" in pair[1]]) / num_steps 

        # length of the list of pairs - and scale it by the shortest path length
        eval_num_steps = num_steps / shortest_step.count("forward")

        for pair in total_response: # mark finished true if agent action is "stop"
            if "stop" in pair[1]:
                eval_finished = True
                break

        return eval_num_questions, eval_num_steps

    def evaluate_response(self, total_response):
        content = [
            {"type": "text", "text": str(total_response)}
        ]
        full_message = [
            {"role": "system", "content": self.base_system_prompt},
            {"role": "user", "content": content}
        ]
        scores = self.client.chat.completions.create(
            model=self.model,
            messages=full_message,
            max_tokens=300
        )
        
        result_text = scores.choices[0].message.content
        result_group = extract_scores(result_text)
        result = result_group
        print("Evaluation Results: ", result)
        print(type(result))
        return result
    
    def calculate_score_with_json(self, log_info:list[dict]):
        result = {
            "num_questions_score": None,
            "num_steps_score": None,
            "action_score": None,
            "question_score": None,
            "stop_distance_score": None, 
            "success": False, 
        }

        shortest_step = log_info[1]["shortest_path"]
        map_config = log_info[0]["map_config"]
        task_config = log_info[0]["task_config"]
        graph = GraphLoader(map_config).construct_graph()
        arrive_threshold = task_config["arrive_threshold"]
        target_position = (task_config["target_infos"][0]["latitude"], task_config["target_infos"][0]["longitude"])
        
        stop_positions = []
        agent_response = []
        for i in range(1, len(log_info)):
            try:
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
                
                if action == "stop":
                    panoid = log_info[i]["current_state"][0]
                    stop_positions.append(graph.get_node_coordinates(panoid))
            
                arrival_status = log_info[i].get("arrival_info")
                if arrival_status is not None:
                    arrival_status = arrival_status[0]["status"]
                if arrival_status:
                    result["success"] = True
            except:
                continue
        
        num_steps = log_info[-1]["forward_ctn"]
        if num_steps == 0:
            return None
        num_q = log_info[-1]["ask_ctn"]
        result["num_questions_score"], result["num_steps_score"], result["action_score"], result["question_score"] = self.calculate_score(agent_response, shortest_step, num_steps=num_steps, num_q=num_q, debug=True)
        result["stop_distance_score"] = self.calculate_stop_distance(stop_positions, target_position, arrive_threshold)
        return result

    def calculate_score(self, total_response:list[str], shortest_step:list, num_steps:int=1, num_q:int=0, debug=False):
        #num_questions, num_steps = self.evaluate_misc(total_response, shortest_step, num_steps, num_questions)
        num_questions_score = num_q/num_steps
        num_steps_score = min(shortest_step.count("forward") / num_steps, 1)
        print(f"num_questions_score: {num_questions_score}, num_steps_score: {num_steps_score}")
        action_score, justification_action = self.evaluate_response(["[ACTION]"] + total_response)
        proactive_score, justification_proactive = self.evaluate_response(["[Q_PROACTIVE]"] + total_response)
        clarification_score, justification_clarification = self.evaluate_response(["[Q_CLARIFICATION]"] + total_response)
        #(action_score, justification_action), (question_score, justification_question) = self.evaluate_response(total_response)
        #print(proactive_score)
        question_score = (int(proactive_score) + int(clarification_score))/2
        justification_question = "Proactive: " + justification_proactive + "Clarification: " + justification_clarification
        if debug:
            print("Action Score: ", action_score)
            print("Action Justification: ", justification_action)
            print("Question Score: ", question_score)
            print("Question Justification: ", justification_question)

        return num_questions_score, num_steps_score, action_score, question_score
    
    def calculate_stop_distance(self, stop_positions, target_position, arrive_threshold):
        if len(stop_positions) == 0:
            return None
        
        distance = 0
        for stop_position in stop_positions:
            distance += max(0, haversine(stop_position, target_position) - arrive_threshold)
        return distance/len(stop_positions)

def parse_task_files(folder_path):
    result = {}
    
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".json"):
            file_path = os.path.join(folder_path, file_name)

            with open(file_path, "r", encoding="utf-8") as file:
                try:
                    data = json.load(file)
                    start_node = data.get("start_node", "")
                    target_infos = data.get("target_infos", [])
                    
                    for target in target_infos:
                        panoid = target.get("panoid", "")
                        name = target.get("name", "")
                        if start_node and panoid:
                            result[f"{start_node}=>{panoid}"] = file_name[:-5]
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON in file {file_name}: {e}")
    
    return result

'''
Actions Taken:
Hallucination: Are the agent's actions completely based on the information it was given? Does it make any unstated or unreasonable assumptions?
5: All of the agent's actions are backed up by the information it was given. It may make inferences, but all of them were drawn logically from given information. If the agent does not have enough information to choose an action, it always select action: ask.
4. Most of the agent's actions are backed up by the information it was given. There are very few instances of making inferences that are not based on the given information. In rare cases, the agent proceeds with a different action where action: ask would be more appropriate.
3. Some of the agent's actions are backed up by the information it was given. The agent makes a fair number of assumptions in its reasoning and can be over confident sometimes. However, it still recognizes the information that it was given and uses the relevant data to inform its decision.
2. Very few of the agent's actions are backed up by the information it was given. The agent makes a wide array of assumptions and sometimes value its own reasoning over concrete information given to it. 
1. Almost none of the agent's actions are backed up by the information it was given. The agent mostly ignores the information that it was given and never selects action: ask to try to learn more information. 

Questions Asked: Evaluations are based on the quality of questions asked by the agent when it is lost. Total score for question is calculated as ([proactive] + [clarification])/2:

[Proactive]: Does the agent ask good proactive questions to gather hints for the next step?
5: The agent consistently asks insightful proactive questions that are relevant and useful.
4: The agent asks proactive questions that are generally relevant but could be more relevant and useful.
3: The agent occasionally asks proactive questions, but they often miss the mark or are too generic.
2: The agent rarely asks proactive questions, and when they do, they are not relevant or useful.
1: The agent does not ask any proactive questions to gather hints for the next step.

[Clarification]: Does the agent ask clarification questions if the answer received is vague?
5: The agent always asks for clarifications when responses are vague, ensuring complete understanding for the next step.
4: The agent usually asks for clarifications on vague responses, but may miss some opportunities.
3: The agent sometimes asks for clarifications, but often proceeds without full clarity.
2: The agent rarely seeks clarifications, leading to misunderstandings or incomplete information.
1: The agent never asks for clarifications, even if the answer it received contains little to no relevant or actionable information.
Note that if the agent did not need to ask any clarification questions because the answers it received was clear, you should give it the same grade for [Clarification] that you gave for [Proactive].
'''

system_prompt = "You are a helpful assistant rating the reasoning and actions of an llm agent trying to navigate to a certain location. You will be given the response history of the agent in the form of a list of strings that contains the context that the agent was given, the action it took and the reasoning of the agent. You are to evaluate ONE of three aspects of the response on a score ranging from 1-5: the quality of reasoning when the agent chooses an action, the proactivity of the agent's questions (if applicable) and the agent's ability to ask clarification questions. Which of these three attributes you evaluate will be prepended in the response history as either [ACTION], [Q_PROACTIVE], or [Q_CLARIFICATION]. When evaluating, closely adhere to the following rubric: Actions Taken([ACTION]): \nHallucination: Are the agent's actions completely based on the information it was given? Does it make any unstated or unreasonable assumptions? 5: All of the agent's actions are backed up by the information it was given. It may make inferences, but all of them were drawn logically from given information. If the agent does not have enough information to choose an action, it always select action: ask. 4. Most of the agent's actions are backed up by the information it was given. There are very few instances of making inferences that are not based on the given information. In rare cases, the agent proceeds with an a different action where action: ask would be more appropriate. 3. Some of the agent's actions are backed up by the information it was given. The agent makes a fair number of assumptions in its reasoning and can be over confident sometimes. However, it still recognizes the information that it was given and uses the relevant data to inform its decision. 2. Very few of the agent's actions are backed up by the information it was given. The agent makes a wide array of assumptions and sometimes value its own reasoning over concrete information given to it.  1. Almost none of the agent's actions are backed up by the information it was given. The agent mostly ignores the information that it was given and never selects action: ask to try to learn more information. \n[Q_PROACTIVE]: Does the agent ask good proactive questions to gather hints for the next step? 5: The agent consistently asks insightful proactive questions that are relevant and useful. 4: The agent asks proactive questions that are generally relevant but could be more relevant and useful. 3: The agent occasionally asks proactive questions, but they often miss the mark or are too generic. 2: The agent rarely asks proactive questions, and when they do, they are not relevant or useful. 1: The agent does not ask any proactive questions to gather hints for the next step. \n[Q_CLARIFICATION]: Does the agent ask clarification questions if the answer received is vague? 5: The agent always asks for clarifications when responses are vague, ensuring complete understanding for the next step. 4: The agent usually asks for clarifications on vague responses, but may miss some opportunities. 3: The agent sometimes asks for clarifications, but often proceeds without full clarity. 2: The agent rarely seeks clarifications, leading to misunderstandings or incomplete information. 1: The agent never asks for clarifications, even if the answer it received contains little to no relevant or actionable information. Your response should be in the following format(do not change what's inside the square bracket): [evaluated_sc_begin] content... [evaluated_sc_end],\n [evaluated_sc_justification_begin] content... [evaluated_sc_justification_end]. Here is an example output: [evaluated_sc_begin]5[evaluated_sc_end],\n [evaluated_sc_justification_begin]The agent did consistently asked questions when it needed to...[evaluated_sc_justification_end]. "
with open("notable_output/log_infos_10.json", "r") as file:
    data = json.load(file)
system_prompt += json2str(data) + "In this response, the agent asks about any specific landmarks or features around Breads Bakery. However, it later asks if there are any landmarks that are nearby the landmarks that it was given. This question is redundant since it is asking for landmarks near the same place multiple times without a good reason to do so. Additionally, the agent receives very specific clues on how to proceed but continues to ask question which is redundant. The agent does ask some proactive questions but due to the issues mentioned, the score for the agent's question asking ability should be a 3. On the other hand, The agent consistently remembers the information it received in the question and answer session and acts based on this. Because of this, it should receive an action score of 5"

actions_rubric = "Actions Taken: \nHallucination: Are the agent's actions completely based on the information it was given? Does it make any unstated or unreasonable assumptions? 5: All of the agent's actions are backed up by the information it was given. It may make inferences, but all of them were drawn logically from given information. If the agent does not have enough information to choose an action, it always select action: ask. 4. Most of the agent's actions are backed up by the information it was given. There are very few instances of making inferences that are not based on the given information. In rare cases, the agent proceeds with a different action where action: ask would be more appropriate. 3. Some of the agent's actions are backed up by the information it was given. The agent makes a fair number of assumptions in its reasoning and can be over confident sometimes. However, it still recognizes the information that it was given and uses the relevant data to inform its decision. 2. Very few of the agent's actions are backed up by the information it was given. The agent makes a wide array of assumptions and sometimes value its own reasoning over concrete information given to it.  1. Almost none of the agent's actions are backed up by the information it was given. The agent mostly ignores the information that it was given and never selects action: ask to try to learn more information."
questions_rubric = "Questions Asked: Evaluations are based on the quality of questions asked by the agent when it is lost. Total score for question is calculated as ([proactive] + [clarification])/2: [Proactive]: Does the agent ask good proactive questions to gather hints for the next step? 5: The agent consistently asks insightful proactive questions that are relevant and useful. 4: The agent asks proactive questions that are generally relevant but could be more relevant and useful. 3: The agent occasionally asks proactive questions, but they often miss the mark or are too generic. 2: The agent rarely asks proactive questions, and when they do, they are not relevant or useful. 1: The agent does not ask any proactive questions to gather hints for the next step. [Clarification]: Does the agent ask clarification questions if the answer received is vague? 5: The agent always asks for clarifications when responses are vague, ensuring complete understanding for the next step. 4: The agent usually asks for clarifications on vague responses, but may miss some opportunities. 3: The agent sometimes asks for clarifications, but often proceeds without full clarity. 2: The agent rarely seeks clarifications, leading to misunderstandings or incomplete information. 1: The agent never asks for clarifications, even if the answer it received contains little to no relevant or actionable information. Note that if the agent did not need to ask any clarification questions because the answers it received was clear, you should give it the same grade for [Clarification] that you gave for [Proactive] and indicate this in your justification."


if __name__=="__main__": 
    task_folder = "config/task/1215_experiment_1"
    task_names = parse_task_files(task_folder)
    log_folder = "output/logs_backup"
    config = {
        "system_prompt": system_prompt,
        "model": "gpt-4o-mini"
    }
    evaluator = AgentEvaluator(config)
    
    cumulative_results = {
        "easy": {
            "num_questions_score": (0, 0), # (cumulative_score, valid_experiments)
            "num_steps_score": (0, 0),
            "action_score": (0, 0),
            "question_score": (0, 0),
            "stop_distance_score": (0, 0), 
            "success_count": (0, 0), 
        }, 
        "medium": {
            "num_questions_score": (0, 0), # (cumulative_score, valid_experiments)
            "num_steps_score": (0, 0),
            "action_score": (0, 0),
            "question_score": (0, 0),
            "stop_distance_score": (0, 0), 
            "success_count": (0, 0), 
        }, 
        "hard": {
            "num_questions_score": (0, 0), # (cumulative_score, valid_experiments)
            "num_steps_score": (0, 0),
            "action_score": (0, 0),
            "question_score": (0, 0),
            "stop_distance_score": (0, 0), 
            "success_count": (0, 0), 
        }
    }

    for root, _, files in tqdm(os.walk(log_folder)):
        for file in files:
            if file.endswith(".json"):
                try:
                    log_path = os.path.relpath(os.path.join(root, file), log_folder)
                    log_path = os.path.join(log_folder, log_path)
                    with open(log_path, "r") as f:
                        data = json.load(f)
                        task_config = data[0]["task_config"]
                        task_name = task_names[task_config["start_node"] + "=>" + task_config["target_infos"][0]["panoid"]]

                        if "eazy" in task_name or "easy" in task_name:
                            difficulty = "easy"
                        elif "middle" in task_name:
                            difficulty = "medium"
                        elif "hard" in task_name:
                            difficulty = "hard"

                        result = evaluator.calculate_score_with_json(data)
                        if result is None:
                            continue

                        # Merge `result` into `cumulative_results`
                        for key in result:
                            if key in cumulative_results[difficulty]:
                                cumulative_score, count = cumulative_results[difficulty][key]
                                if result[key] is None:
                                    continue
                                result[key] = float(result[key])
                                if result[key] is not None:  # Ensure the score is valid
                                    cumulative_results[difficulty][key] = (
                                        cumulative_score + result[key],
                                        count + 1
                                    )
                            elif key == "success":
                                cumulative_success, total = cumulative_results[difficulty]["success_count"]
                                cumulative_results[difficulty]["success_count"] = (
                                    cumulative_success + (1 if result["success"] else 0),
                                    total + 1
                                )
                except Exception as e:
                    print(f"Error processing {log_path}: {e}")
                    continue

    # Calculate averages
    final_results = {}
    for difficulty, metrics in cumulative_results.items():
        final_results[difficulty] = {}
        for metric, (cumulative_score, count) in metrics.items():
            if metric == "success_count":
                success, total = cumulative_score, count
                final_results[difficulty]["success_rate"] = success / total if total > 0 else 0
            else:
                final_results[difficulty][metric] = cumulative_score / count if count > 0 else 0

    # Output final results
    print("Final Results:")
    print(json.dumps(final_results, indent=4))
    print(cumulative_results)

    # error_log = r"output\logs_backup\run_batch_4\20241216-073752_logs\log_infos_82.json"
    # fail_log = r"output\logs_backup\run_batch_4\20241216-175030_logs\log_infos_151.json"
    # success_log = r"output\logs_backup\run_batch_2_20241216_0019\20241215-235712_logs_success!!!\log_infos_27.json"

    # with open(error_log, "r") as file:
    #     data = json.load(file)
    # print(evaluator.calculate_score_with_json(data))
