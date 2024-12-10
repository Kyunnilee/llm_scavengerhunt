# -*- coding:utf-8 -*-

import os
import sys

import warnings

import config.openai_oracle as openai_oracle
from openai_agent import OpenAIAgent

class Oracle(): 
    def __init__(self, oracle_config: dict): 
        
        warnings.warn(
            "oracle_config is deprecated and will be removed in a future version. "
            "Please use config/openai_oracle.py instead.",
            FutureWarning,
            stacklevel=2
        )

        # self.mode is gpt model or human
        # self.question is question sent from QA_Agent to Navi_Agent
        self.model = openai_oracle.model
        self.question = openai_oracle.question_to_navi
        self.agent = None

        self.latest_world_states = None
        self.latest_clues = None

        if self.model == "human":
            pass
            
        elif self.model.startswith("gpt-"):
            cfg = {
                "model": openai_oracle.model, 
                "policy": openai_oracle.init_prompt
            }
            self.agent = OpenAIAgent(cfg)
            print(f"Loaded QA Prompts from {qa_agent.__file__}")

    def update_observations(self, world_states, clues):
        """
        Updates oracle's observation of world_states and additional clues.
        """
        self.latest_world_states = world_states
        self.clues = clues

    def get_answer(self, question): 
        """
        Get answer from QA_Agent.
        MUST call update_observations BEFORE.
        Otherwise, the behavior is undefined.
        """
        if self.model == "human": 
            print(f"Question: {question}")
            answer = input("Enter the answer: ")
        
        elif self.model.startswith("gpt-"):
            pass

        return answer

    def _translate_path(self, path: list[str]):
        input_message = "Turn this path into human-friendly navigation text.\n"
        input_message += "".join(path)
        text_navigation = self.send_message(input_message)
        return text_navigation


if __name__ == "__main__":
    qa_agent = Oracle()

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
