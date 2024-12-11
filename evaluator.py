from openai import OpenAI
import os
import json
import ast

api_key=os.environ.get("OPENAI_API_KEY")
TODO = ""
class AgentEvaluator:
    def __init__(self, config): 
        self.client = OpenAI(api_key=api_key)
        self.base_system_prompt = config['system_prompt']
        self.model = config['model']

    
    def evaluate_misc(self, total_response, shortest_step, current_pos, target_pos):
        '''
        Evaluate the number of questions asked (int), number of steps took to reach destination (int), and whether the agent finished (bool)

        total_response: List of pairs in the following format [("Context: " + message, "Agent Action: " + action)]/ One node, one action
        '''
        # total_response = list of "Context message and action message string" 
        num_steps = 0 # num of Forwards
        eval_num_questions, eval_num_steps = 0, 0 # evaluated benchmark value of # questions and 3 steps taken
        eval_finished = current_pos == target_pos # evaluated benchmark value whether the agent reached the goal or not

        num_steps = len([pair for pair in total_response if "forward" in pair[1]])
        eval_num_questions = len([pair for pair in total_response if "lost" in pair[1]]) / num_steps 

        # length of the list of pairs - and scale it by the shortest path length
        eval_num_steps = num_steps / shortest_step

        for pair in total_response: # mark finished true if agent action is "stop"
            if "stop" in pair[1]:
                eval_finished = True
                break

        return eval_num_questions, eval_num_steps, eval_finished

    
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
        result = ast.literal_eval(scores.choices[0].message.content)
        print("Evaluation Results: ", result)
        print(type(result))
        return result

    def calculate_score(self, total_response, shortest_step, world_states, debug=False):
        current_pos = world_states["abs_curr_pos"]
        target_pos = world_states["abs_target_pos"]
        num_questions, num_steps, finished = self.evaluate_misc(total_response, shortest_step, current_pos, target_pos)
        (action_score, justification_action), (question_score, justification_question) = self.evaluate_response(total_response)

        if debug:
            print("Action Score: ", action_score)
            print("Action Justification: ", justification_action)
            print("Question Score: ", question_score)
            print("Question Justification: ", justification_question)
            print(f"num_questions: {num_questions}, num_steps: {num_steps}, finished: {finished}")


        # Current implementation does not use for loops, should change to this if the prompt size becomes too big
        # for response in agent_lost:
        #     lost_scores.append(self.evaluate_lost_response(response))
        
        # for response in agent_move:
        #     move_scores.append(self.evaluate_move_response(response))
        
        
        return num_questions, num_steps, finished, action_score, question_score
'''
Actions Taken:
Hallucination: Are the agent's actions completely based on the information it was given? Does it make any unstated or unreasonable assumptions?
5: All of the agent's actions are backed up by the information it was given. It may make inferences, but all of them were drawn logically from given information. If the agent does not have enough information to choose an action, it always select action: lost.
4. Most of the agent's actions are backed up by the information it was given. There are very few instances of making inferences that are not based on the given information. In rare cases, the agent proceeds with a different action where action: lost would be more appropriate.
3. Some of the agent's actions are backed up by the information it was given. The agent makes a fair number of assumptions in its reasoning and can be over confident sometimes. However, it still recognizes the information that it was given and uses the relevant data to inform its decision.
2. Very few of the agent's actions are backed up by the information it was given. The agent makes a wide array of assumptions and sometimes value its own reasoning over concrete information given to it. 
1. Almost none of the agent's actions are backed up by the information it was given. The agent mostly ignores the information that it was given and never selects action: lost to try to learn more information. 

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
actions_rubric = "Actions Taken: \nHallucination: Are the agent's actions completely based on the information it was given? Does it make any unstated or unreasonable assumptions? 5: All of the agent's actions are backed up by the information it was given. It may make inferences, but all of them were drawn logically from given information. If the agent does not have enough information to choose an action, it always select action: lost. 4. Most of the agent's actions are backed up by the information it was given. There are very few instances of making inferences that are not based on the given information. In rare cases, the agent proceeds with a different action where action: lost would be more appropriate. 3. Some of the agent's actions are backed up by the information it was given. The agent makes a fair number of assumptions in its reasoning and can be over confident sometimes. However, it still recognizes the information that it was given and uses the relevant data to inform its decision. 2. Very few of the agent's actions are backed up by the information it was given. The agent makes a wide array of assumptions and sometimes value its own reasoning over concrete information given to it.  1. Almost none of the agent's actions are backed up by the information it was given. The agent mostly ignores the information that it was given and never selects action: lost to try to learn more information."

# TODO: Questions Rubric:
questions_rubric = "Questions Asked: Evaluations are based on the quality of questions asked by the agent when it is lost. Total score for question is calculated as ([proactive] + [clarification])/2: [Proactive]: Does the agent ask good proactive questions to gather hints for the next step? 5: The agent consistently asks insightful proactive questions that are relevant and useful. 4: The agent asks proactive questions that are generally relevant but could be more relevant and useful. 3: The agent occasionally asks proactive questions, but they often miss the mark or are too generic. 2: The agent rarely asks proactive questions, and when they do, they are not relevant or useful. 1: The agent does not ask any proactive questions to gather hints for the next step. [Clarification]: Does the agent ask clarification questions if the answer received is vague? 5: The agent always asks for clarifications when responses are vague, ensuring complete understanding for the next step. 4: The agent usually asks for clarifications on vague responses, but may miss some opportunities. 3: The agent sometimes asks for clarifications, but often proceeds without full clarity. 2: The agent rarely seeks clarifications, leading to misunderstandings or incomplete information. 1: The agent never asks for clarifications, even if the answer it received contains little to no relevant or actionable information. Note that if the agent did not need to ask any clarification questions because the answers it received was clear, you should give it the same grade for [Clarification] that you gave for [Proactive] and indicate this in your justification."

if __name__=="__main__": 
    test_prompt = """You are a helpful assistant rating the reasoning and actions of an llm agent trying to navigate to a certain location. You will be given the response history of the agent in the form a stringified list of pairs. Each pair will contain the context that the agent was given and action that it took. You are to evaluate two aspects of the response on a score ranging from 1-5: the quality of reasoning when the agent chooses an action and the quality of questions that the agent asks if it is lost. IMPORTANT NOTE: when you evaluate the quality of questions, you are grading the questions themselves. Whether the question was needed or not will be graded when accessing the first score(quality of reasoning). If the response contains no questions, you should make the question quality score a -1. Here are the rubrics for grading the agent's action reasoning and questions: """ + actions_rubric + questions_rubric + "Your response should be two pairs in the following format: (action_reasoning_score, justification_for_score), (question_score, justification_for_score). Example: (5, JUSTIFICATION_HERE), (3, JUSTIFICATION_HERE). Make sure that any inner quotes are properly escaped."
    test_config = {
        'system_prompt': test_prompt, 
        'model': 'gpt-4o-mini' 
    }

    with open("evaluator.json", "w") as json_file:
        json.dump(test_config, json_file, indent=4)

    sample_response = [("Context: You are currently at 37.7803403, -122.4180816 facing 82.663787322416.The five images below show the view in different directions, they are on your left, front-left, front, front-right, and right. Once you have decided which action to take, you can forget about the images.\nYou can take following action: Current graph state: ('4018889690', 82.663787322416)\nAvailable next actions and graph states:\nAction: forward, to graph state: ('3999644793', 82.6656211991133)\nAction: right, heading: 148.968704267527\nAction: lost, ask for help.\nAction: stop, end the navigation.\nChoose the option that will make your heading around 149", 'Agent Action: right'), ("Context: You are currently at 37.7803403, -122.4180816 facing 148.968704267527.The five images below show the view in different directions, they are on your left, front-left, front, front-right, and right. Once you have decided which action to take, you can forget about the images.\nYou can take following action: Current graph state: ('4018889690', 148.968704267527)\nAvailable next actions and graph states:\nAction: forward, to graph state: ('4018889698', 140.44581646108813)\nAction: left, heading: 82.663787322416\nAction: right, heading: -97.13931973253575\nAction: lost, ask for help.\nAction: stop, end the navigation.\nChoose the option that will get you to the graph state: ('4018889698', 140.44581646108813)", 'Agent Action: forward'), ("Context: You are currently at 37.7803029, -122.4180591 facing 140.44581646108813.The five images below show the view in different directions, they are on your left, front-left, front, front-right, and right. Once you have decided which action to take, you can forget about the images.\nYou can take following action: Current graph state: ('4018889698', 140.44581646108813)\nAvailable next actions and graph states:\nAction: forward, to graph state: ('4018889725', 128.2695160626994)\nAction: turn_around, heading: -31.031295732473033\nAction: lost, ask for help.\nAction: stop, end the navigation.\nChoose the option that will get you to the graph state: ('4018889725', 128.2695160626994)", 'Agent Action: forward'), ("Context: You are currently at 37.7802759, -122.4180368 facing 128.2695160626994.The five images below show the view in different directions, they are on your left, front-left, front, front-right, and right. Once you have decided which action to take, you can forget about the images.\nYou can take following action: Current graph state: ('4018889725', 128.2695160626994)\nAvailable next actions and graph states:\nAction: forward, to graph state: ('4018889735', 112.96833410760605)\nAction: turn_around, heading: -39.554183538911886\nAction: lost, ask for help.\nAction: stop, end the navigation.\nChoose the option that will get you to the graph state: ('4018889735', 112.96833410760605)", 'Agent Action: forward'), ("Context: You are currently at 37.7802546, -122.4180098 facing 112.96833410760605.The five images below show the view in different directions, they are on your left, front-left, front, front-right, and right. Once you have decided which action to take, you can forget about the images.\nYou can take following action: Current graph state: ('4018889735', 112.96833410760605)\nAvailable next actions and graph states:\nAction: forward, to graph state: ('298077885', 102.4433342028448)\nAction: turn_around, heading: -51.730483937300605\nAction: lost, ask for help.\nAction: stop, end the navigation.\nChoose the option that will make your heading = -51.730483937300605", 'Agent Action: turn_around'), ("Context: You are currently at 37.7802546, -122.4180098 facing -51.730483937300605.The five images below show the view in different directions, they are on your left, front-left, front, front-right, and right. Once you have decided which action to take, you can forget about the images.\nYou can take following action: Current graph state: ('4018889735', -51.730483937300605)\nAvailable next actions and graph states:\nAction: forward, to graph state: ('4018889725', -39.554183538911886)\nAction: turn_around, heading: 112.96833410760605\nAction: lost, ask for help.\nAction: stop, end the navigation.\nChoose the option stop", 'Agent Action: stop')]

    evaluator = AgentEvaluator(test_config)
    evaluator.calculate_score(sample_response, 1, debug=True)