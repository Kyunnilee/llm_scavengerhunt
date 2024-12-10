# -*- coding:utf-8 -*-

model = "gpt-4o-mini"

# ======================== INIT PROMPT ========================

qa_init_prompt = \
"""You are a helpful agent specialized in answering navigation-related questions within a game.

In this game, there is a testing agent (not you) who may ask for guidance if he gets lost. 
He might pose questions such as: "What is the relative position of my target to me?" or "How do I get from my location to my target?"

Each time the testing agent asks a question, we will provide you with relevant world state information about the game. 
Use this information to craft accurate and helpful responses to assist the testing agent in reaching his target.
Make sure to keep your tone natural and friendly, as if you were speaking to a human. 
This will help the testing agent feel comfortable and confident while navigating.
"""

# =========== QUESTION FROM ORACLE TO NAVI AGENT ==============

qa_question_to_navi = \
"""What is your question? 
Just tell me your question, don't give action this time.
"""

# ===================== WORLD STATE PROMPT ====================

# Note that the arguments in <<<>>> will be replaced in qa_agent by real arguments.
qa_final_prompt = qa_init_prompt + \
"""Now the game has begun, and the testing agent DO GETS LOST.
Here is the world states provided. Please generate a proper answer to the testing agent.

[World States Provided as Follows:]
The target's exact latitude and longtitude is: <<<abs_target_pos>>>
The absolute location of the target position is: at the <<<abs_target_dir>>> of the current map.

The current exact latitude and longtitude is: <<<abs_curr_pos>>>
The absolute location of the current position is: at the <<<abs_curr_dir>>> of the current map.

The distance from current location to target location is <<<abs_euclidean_dist>>> meters.

The relative position of the target to the current location is: <<<rel_target_pos>>>
The relative position of the current position to the target is: <<<rel_curr_pos>>>

The path from current location to target location is: <<<path_description>>>
[World States Ends]

[Question from the Testing Agent: ]
<<<Testing_Agent_Question>>>
"""

# ============ HELPER: QUESTION EVALUATION PROMPT =============

eval_init_prompt = \
"""You are tasked with evaluating the quality of a navigation question. 
The question may ask how to get from point A to point B on a map. If it is not about the path from point A to point B on the map, directly output "Irrelevant" and end your answer.
If it IS a question about the path from point A to point B on a map, your goal is to assess how specific and clear the question is. Consider the following criteria:

Clarity: Does the question clearly describe the locations of point A and point B? Are any important landmarks or details mentioned?
Specificity: Does the question provide enough detail to make the answer actionable? For example, does it ask about specific directions (e.g., turn left, move forward a certain number of steps) or provide relevant context (e.g., intersections, landmarks)?
Ambiguity: Is the question too vague or open to interpretation? Does it lack necessary details, such as the starting point's orientation, the type of path, or any nearby landmarks?
Relevance: Does the question focus on the essential aspects of navigation, or does it contain unnecessary information?
Example Questions:

1. "How do I get from the city center to the park?"
Ans: This question is vague. It doesn't specify the exact location within the city center, and there's no detail about the route or any landmarks along the way.

2. "What is the fastest route from the north side of the city to the park located on Main Street?"
This is more specific, as it mentions both the starting location (north side of the city) and the destination (park on Main Street), providing clear information about the route.

3. "How do I get from the intersection of Fifth Avenue and Oak Street to the library on Maple Street?"
This is a highly specific question, as it provides exact locations and landmarks, making it easy to understand and answer with precision.

Scoring Criteria:
1. Good (Score: 3): The question is highly specific, with clear details on both the starting point and destination, and it may also include relevant context such as intersections, landmarks, or specific directions.
2. Median (Score: 2): The question provides some detail but lacks important specifics or clarity. It might mention the general area but not precise locations, or it may have some ambiguity that requires clarification.
3. Poor (Score: 1): The question is vague or missing essential details. It may be unclear about the starting point, destination, or the type of path, making it difficult to answer effectively.

Final Evaluation: After reviewing the question, assign a score based on the scale above:
1. Good = 3
2. Median = 2
3. Poor = 1

Please provide your justifying reasons in the first line, followed by a single score (1-3) on the second line.
"""

eval_final_prompt = eval_init_prompt + \
"""Here is the question to be evaled: 
"<<<evaled_question>>>"
"""

# ============= HELPER: PATH TRANSLATING PROMPT ===============

path_translate_prompts = {
    "level_1": "", 
    "level_2": "", 
    "level_3": "", 
}

path_translate_prompts["level_1"] = \
"""You should translate a relative direction to a very general path.
Here is an example:

Our input:
The relative location of the target is Forward-Right.

Your output should be like:
The target is at your forward-right, so go forward first and then go right somewhere.

Now the real input is:
The relative location of the target is <<<rel_target_pos>>>

Please provide the desired output.
"""

path_translate_prompts["level_2"] = \
"""
You should translate sequence of actions [Forward, Left, Right, Turn_Around] into human-friendly navigation text. 
You are eager to make the text short and simplified.
Specifically, there will be a graph consisted of nodes and edges. A game player can move along that graph, using options [Forward, Left, Right, Turn_Around]. 
When that player calls "Forward", he will move forward by one node.
When that player calls "Right", "Left" or "Turn_Around", he will change his looking-at direction and sticks to his original position.
When the player gets lost, we will provide him a path from his current node to target node. 
You should translate this path into clear, human-readable text. Here is an example:

Our input: 
At \"Bancoft Street\"
Action: Forward"
Action: Forward.
Action: Forward.
Action: Turn Right.
Action: Turn Right.
Action: Forward. 
At: \"Shuttuck Avenue\"
Action: Forward.
Action: Stop.

Your output should look like:
Move forward a couple of steps, then turn right. Move forward to reach your target.

Now the real input is: 
<<<path_action>>>

Please provide the desired output.
"""

path_translate_prompts["level_3"] = \
"""You should translate sequence of actions [Forward, Left, Right, Turn_Around] into human-friendly navigation text. You are eager to make the text detailed and clear.
Specifically, there will be a graph consisted of nodes and edges. A game player can move along that graph, using options [Forward, Left, Right, Turn_Around]. 
When that player calls "Forward", he will move forward by one node.
When that player calls "Right", "Left" or "Turn_Around", he will change his looking-at direction and sticks to his original position.
When the player gets lost, we will provide him a path from his current node to target node. 
You should translate this path into clear, human-readable text. Here is an example:

Our input: 
At \"Bancoft Street\"
Action: Forward"
Action: Forward.
Action: Forward.
Action: Turn Right.
Action: Turn Right.
Action: Forward. 
At: \"Shuttuck Avenue\"
Action: Forward.
Action: Stop.

Your output should look like: 
You are at \"Bancoft Street\" now. Start by moving forward for three steps. "
Next, you will reach the intersection of \"Bancoft Street\" and \"Shuttuck Avenue\". "
Turn right TWICE at this point. This will orient you properly at the intersection. Afterward, proceed forward for two more steps. "
You will arrive at your target. Use action \"Stop\" once you reach it."

Now the real input is: 
<<<path_action>>>

Please provide the desired output.
"""

# ======================== MORE PROMPT ========================

"""whatttt"""
