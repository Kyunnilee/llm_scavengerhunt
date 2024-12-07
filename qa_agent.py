# -*- coding:utf-8 -*-

import os
import sys

import config.qa_config as qa_config
from openai_agent import OpenAIAgent

class QA_Agent(OpenAIAgent):
    def __init__(self):
        cfg = {
            "model": qa_config.model, 
            "policy": qa_config.init_prompt
        }
        super().__init__(cfg)

        # add more prompts here that we can call in the following functions
        self.path_translate_prompts = qa_config.path_translate_prompts

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
