# -*- coding:utf-8 -*-

import os
import re
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
        self.question = openai_oracle.qa_question_to_navi

        self.qa_agent = None
        self.eval_agent = None
        self.translate_path_agent = None

        self.latest_world_states = None
        self.latest_clues = None

        if self.model == "human":
            pass
            
        elif self.model.startswith("gpt-"):
            cfg_qa = {
                "model": openai_oracle.model, 
                "policy": openai_oracle.qa_init_prompt
            }
            self.qa_agent = OpenAIAgent(cfg_qa)

            cfg_eval = {
                "model": openai_oracle.model, 
                "policy": openai_oracle.eval_init_prompt
            }
            self.eval_agent = OpenAIAgent(cfg_eval)

            cfg_translate = {
                "model": openai_oracle.model, 
                "policy": openai_oracle.path_translate_init_prompt
            }
            self.path_translate_agent = OpenAIAgent(cfg_translate)

            print(f"Loaded QA Prompts from {openai_oracle.__file__}")

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
            question_detail_level = self._eval_question(question)
            print(f"[[Logs]]: question detail level evaluated as level [{question_detail_level}]")
            if question_detail_level is None:
                path_description = "Not provided for this question"
            else:
                path_description = self._translate_path(
                    path=self.latest_world_states["path_action"], 
                    detail_level=question_detail_level
                )
                print(f"path description generated")
            
            qa_prompt = openai_oracle.qa_final_prompt

            qa_prompt = qa_prompt.replace("<<<abs_target_pos>>>", str(self.latest_world_states["abs_target_pos"]))
            qa_prompt = qa_prompt.replace("<<<abs_target_dir>>>", self.latest_world_states["abs_target_dir"])
            qa_prompt = qa_prompt.replace("<<<abs_curr_pos>>>", str(self.latest_world_states["abs_curr_pos"]))
            qa_prompt = qa_prompt.replace("<<<abs_curr_dir>>>", self.latest_world_states["abs_curr_dir"])
            qa_prompt = qa_prompt.replace("<<<abs_euclidean_dist>>>", str(self.latest_world_states["abs_euclidean_dist"]))
            qa_prompt = qa_prompt.replace("<<<rel_target_pos>>>", str(self.latest_world_states["rel_target_pos"]))
            qa_prompt = qa_prompt.replace("<<<rel_curr_pos>>>", str(self.latest_world_states["rel_curr_pos"]))
            qa_prompt = qa_prompt.replace("<<<path_description>>>", path_description)
            qa_prompt = qa_prompt.replace("<<<Testing_Agent_Question>>>", question)

            answer = self.qa_agent.send_message(qa_prompt)

        return answer

    def _eval_question(self, question):
        eval_prompt = openai_oracle.eval_final_prompt
        eval_prompt = eval_prompt.replace("<<<evaled_question>>>", question)
        answer = self.eval_agent.send_message(eval_prompt)

        if "Irrelevant" in answer:
            return None
        else:
            return self._parse_score(answer)

    def _translate_path(self, path: list[str], detail_level: int):
        """
        Assumes detail_level: int in [1, 3], valid levels.
        Returns translated path (from list[str] to human friendly text)
        """
        input_message = openai_oracle.path_translate_prompts[f"level_{detail_level}"]
        if detail_level == 1:
            input_message = input_message.replace("<<<rel_target_pos>>>", self.latest_world_states["rel_target_pos"])
        elif detail_level in [2, 3]:
            path = list(map(lambda x: "Action: " + x, path))
            path_text = "\n".join(path)
            input_message = input_message.replace("<<<path_action>>>", path_text)

        text_navigation = self.path_translate_agent.send_message(input_message)
        return text_navigation

    def _parse_score(self, input_str):
        """
        Example:
        Input: "abc1d2ef3gh123"
        Output: ['1', '2', '3', '1', '2', '3']
        """
        pattern = r'[123]'
        found = re.findall(pattern, input_str)
        return list(map(int, found))[-1]


if __name__ == "__main__":
    qa_agent = Oracle()

