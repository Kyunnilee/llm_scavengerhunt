from openai import OpenAI
import os 

api_key=os.environ.get("OPENAI_API_KEY")
TODO = ""
class AgentEvaluator:
    def __init__(self, config): 
        self.client = OpenAI(api_key=api_key)
        self.base_system_prompt = config['system_prompt']
        self.image_system = config['image_system']
        self.model = config['model']

    
    def evaluate_misc(self, total_response, shortest_step):
        '''
        Evaluate the number of questions asked (int), number of steps took to reach destination (int), and whether the agent finished (bool)

        total_response: List of pairs in the following format [("Context: " + message, "Agent Action: " + action)]/ One node, one action
        '''
        # total_response = list of "Context message and action message string" 
        num_steps = 0 # num of Forwards
        eval_num_questions, eval_num_steps = 0 # evaluated benchmark value of # questions and 3 steps taken
        eval_finished = False # evaluated benchmark value whether the agent reached the goal or not

        num_steps = len([pair for pair in total_response if "forward" in pair[1]])
        eval_num_questions = len([pair for pair in total_response if "lost" in pair[1]]) / num_steps 

        # length of the list of pairs - and scale it by the shortest path length
        eval_num_steps = num_steps / shortest_step

        for pair in total_response: # mark finished true if agent action is "stop"
            if "stop" in pair[1]:
                eval_finished = True
                break

        return eval_num_questions, eval_num_steps, eval_finished

    # def evaluate_lost_response(self, response):
    #     pass

    # def evaluate_move_response(self, response):
    #     message, action = response
    #     content = [
    #         {"type": "text", "text": "Here is the context: " + message},
    #         {"type": "text", "text": "Here is the action chosen by the agent: " + action}
    #     ]
    #     full_message = [
    #         {"role": "system", "content": self.base_system_prompt},
    #         {"role": "user", "content": contet}
    #     ]
    #     movement_score, justification = self.client.chat.completions.create(
    #         model=self.model,
    #         messages=full_message,
    #         max_tokens=300
    #     )
        
    #     return movement_score
    
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
        
        return scores

    def calculate_score(self, total_response):
        num_questions, num_steps, finished = self.evaluate_misc(total_response)
        (action_score, justification_action), (question_score, justification_question) = self.evaluate_response(total_response)

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
4. Most of the agent's actions are backed up by the information it was given. There are very few instances of making inferences that are not based on the given information. In rare cases, the agent proceeds with an a different action where action: lost would be more appropriate.
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
1: The agent never asks for clarifications, regardless of the clarity of the recevied answers.

'''
actions_rubric = "Actions Taken: \nHallucination: Are the agent's actions completely based on the information it was given? Does it make any unstated or unreasonable assumptions? 5: All of the agent's actions are backed up by the information it was given. It may make inferences, but all of them were drawn logically from given information. If the agent does not have enough information to choose an action, it always select action: lost. 4. Most of the agent's actions are backed up by the information it was given. There are very few instances of making inferences that are not based on the given information. In rare cases, the agent proceeds with an a different action where action: lost would be more appropriate. 3. Some of the agent's actions are backed up by the information it was given. The agent makes a fair number of assumptions in its reasoning and can be over confident sometimes. However, it still recognizes the information that it was given and uses the relevant data to inform its decision. 2. Very few of the agent's actions are backed up by the information it was given. The agent makes a wide array of assumptions and sometimes value its own reasoning over concrete information given to it.  1. Almost none of the agent's actions are backed up by the information it was given. The agent mostly ignores the information that it was given and never selects action: lost to try to learn more information."

# TODO: Questions Rubric:
questions_rubric = TODO

if __name__=="__main__": 
    test_prompt = """You are a helpful assistant rating the reasoning and actions of an llm agent trying to navigate to a certain location. You will be given the response history of the agent in the form a stringified list of pairs. Each pair will contain the context that the agent was given and action that it took. You are to evaluate two aspects of the response on a score ranging from 1-5: the quality of reasoning when the agent chooses an action and the quality of questions that the agent asks if it is lost. To elaborate, here are the rubrics for grading the agent's action reasoning and questions: """ + actions_rubric + questions_rubric + "Your response should be two pairs in the following format: (action_reasoning_score, justification_for_score), (question_score, justification_for_score)."
    test_config = {
        'system_prompt': test_prompt, 
        'model': 'gpt-4o-mini' 
    }
