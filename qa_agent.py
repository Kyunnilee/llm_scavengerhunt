# -*- coding:utf-8 -*-

import os
import sys

import config.openai_oracle as openai_oracle
from openai_agent import OpenAIAgent

class Oracle(): 
    def __init__(self, oracle_config: dict): 
        # self.mode is gpt model or human
        # self.question is question sent from QA_Agent to Navi_Agent
        self.mode = oracle_config["mode"]
        self.question = oracle_config["question"] 

        if self.mode == "human":
            pass
            
        elif self.mode.startswith("gpt-"):
            cfg = {
                "model": oracle_config["mode"], 
                "policy": openai_oracle.init_prompt
            }
            super().__init__(cfg)
            print(f"Loaded QA Prompts from {qa_agent.__file__}")

        oracle_agent_prompt = oracle_config["prompt"]
        llm_config = {
            "config_list": [{
                "model": "gpt-4o-mini", 
                "api_key": os.environ.get("OPENAI_API_KEY")
            }]
        }
        
        print(f"Loaded QA Config from json")

    def get_answer(self, question): 
        #TODO get answer from the model 
        if self.mode == "human": 
            print(f"Question: {question}")
            answer = input("Enter the answer: ")
        return answer

class QA_Agent(OpenAIAgent):
    def __init__(self):
        
        # add more prompts here that we can call in the following functions
        self.path_translate_prompts = openai_oracle.path_translate_prompts

    def ask(self, question):
        # 1. identify what the question is for 
        # (e.g. general_path, distance, next_step, next_multi_steps)
        question_type = self.send_message


    def translate_path(self, path: list[str]):
        input_message = "Turn this path into human-friendly navigation text.\n"
        input_message += "".join(path)
        text_navigation = self.send_message(input_message)
        return text_navigation

if __name__ == "__main__":
    qa_agent = QA_Agent()

    correct_path = [
        "At: Deleware Street; Go: Forward\n", 
        "Go: Forward\n", 
        "Go: Forward\n", 
        "Go: Forward\n", 
        "At: Deleware Street; Turn: Left;\n", 
        "At: Deleware Street; Turn: Left;\n", 
        "At: Deleware Street; Turn: Left;\n", 
        "Go: Forward; At: Virginia Street\n", 
        "Go: Forward\n", 
        "Stop.", 
    ]
    ans = qa_agent.translate_path(correct_path)
    print(ans)
