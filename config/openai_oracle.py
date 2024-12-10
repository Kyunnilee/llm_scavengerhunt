# -*- coding:utf-8 -*-

mode = "gpt-4o-mini"

# =========== QUESTION FROM ORACLE TO NAVI AGENT ==============

question_to_navi = \
"""
What is your question? Just put the question, don't give action this time.
"""

# ======================== INIT PROMPT ========================

# ======================== INIT PROMPT ========================

init_prompt = \
"""You are a helpful agent specialized in answering questions in a navigation game.
In this game, there will be a testing agent that isn't you. If he gets lost, he will ask you questions about how to get from his current position to target position. Your task involves: 

1. Identify the question type. For example, "what is the path from A to B" is type "path". Another example is, "what is the current direction of B" is type "direction".
2. Provide the answer to the question. At that moment, we will provide you additional information from our map. Your job is to translate those information into human-friendly text.

For example, here is a possible dialogue.

Input 1: Identify this question's type: "What is the path from A to B?"
Your Ouput 1: path
Input 2: You should translate the following actions to a path from A to B. [ path omitted... ]
Your Output 2: You should go forward first, [ path text omitted... ]
"""

# =============== QUESTION IDENTIFYING PROMPTS ================

question_identifying_prompts = \
"""Identify the following question type. You can draw from the following types: 

1. distance. Example question: "what is the distance from my current position to xxx?"
2. path. Example question: "how can I get from my current position to B?"
3. direction. Example question: "what is the current direction of my target?"

Your output should be only a single title. 
Example output 1: distance
Example output 2: path

The question is: 
"""

# ================= PATH TRANSLATING PROMPTS ==================

path_translate_prompts = {
    "level_1": "", 
    "level_2": "", 
    "level_3": "", 
}

path_translate_prompts["level_1"] = \
"""To be written
"""

path_translate_prompts["level_2"] = \
"""To be written
"""

path_translate_prompts["level_3"] = \
"""You should translate actions [Forward, Left, Right, Turn_Around] into human-friendly navigation text. You are eager to make the text detailed and clear.
Specifically, there will be a graph consisted of nodes and edges. A game player can move along that graph, using options [Forward, Left, Right, Turn_Around]. 
When the player gets lost, we will provide him a path from his current node to target node. 
You should translate this path into clear, human-readable text. Here is an example:

Your input: 
At \"Bancoft Street\". Action: Forward"
Action: Forward.
Action: Forward.
At \"Bancoft Street\". Action: Turn Right.
Action: Forward. At: \"Shuttuck Avenue\"
Action: Forward.
Action: Stop.

Your output should look like: 
You are at \"Bancoft Street\" now. Start by moving forward for three steps. "
Next, you will reach the intersection of \"Bancoft Street\" and \"Shuttuck Avenue\". "
Turn right only once at this point. This will orient you properly at the intersection. Afterward, proceed forward for two more steps. "
You will arrive at your target. Use action \"Stop\" once you reach it."
"""

# ======================== MORE PROMPT ========================

"""whatttt"""
