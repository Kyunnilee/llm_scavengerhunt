from openai import OpenAI
import os
import json

api_key=os.environ.get("OPENAI_API_KEY")
TODO = ""
class AgentEvaluator:
    def __init__(self, config): 
        self.client = OpenAI(api_key=api_key)
        self.base_system_prompt = config['system_prompt']
        self.image_system = config['image_system']
        self.model = config['model']

    
    def evaluate_misc(self, total_response):
        '''
        Evaluate the number of questions asked (int), number of steps took to reach destination (int), and whether the agent finished (bool)

        total_response: List of pairs in the following format [("Context: " + message, "Agent Action: " + action)]
        '''
        # TODO: Implement this method
        num_questions, num_steps, finished = None

        return num_questions, num_steps, finished

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
    #         {"role": "user", "content": content}
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
        (action_score, justification_action), (question_score, justification_question) = self.evaluate_response(str(total_response))

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

Questions Asked:


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

    with open("evaluator.json", "w") as json_file:
        json.dump(test_config, json_file, indent=4)
