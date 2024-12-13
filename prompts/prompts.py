# Step 1: Give specific directional instructions (ex: left -> right -> forward)
# Step 2: Give positional information (ex: (0,0) -> (1,1))
# Step 3: Give landmark information (ex: go in the direction of the JC Penny)
# Up until this point, there should be instructions that specifies every move
# now, things can be more general/abstract
# Step 4: Give landmark information (ex: keep going forward until you see a no u-turn sign, turn right at this sign)
# Step 5: Give landmark information with incomplete information (ex: keep going forward until you see the light)
# (In above case, the place that the agent stops at will either only have a right or forward option, or the target will be 
# visible in the right, the agent will be responsible for making this inference and taking a right turn)
# Step 6: Give no information

# NAVIGATION_LVL_1 = ["Among these options, choose the action: right", "Among these options, choose the action: forward", "Among these options, choose the action: forward", "Among these options, choose the action: forward", "Among these options, choose the action: turn_around", "Among these options, choose the action: stop"]
# NAVIGATION_LVL_1 = ["Among these options, choose the action: turn_around", "Among these options, choose the action: forward", "Among these options, choose the action: stop"]
# NAVIGATION_LVL_2 = ["Choose the option that will make your heading around 149", "Choose the option that will get you to the graph state: ('4018889698', 140.44581646108813)", "Choose the option that will get you to the graph state: ('4018889725', 128.2695160626994)", "Choose the option that will get you to the graph state: ('4018889735', 112.96833410760605)", "Choose the option that will make your heading = -51.730483937300605", "Choose the option stop"]

NAVIGATION_LVL_1 = []
NAVIGATION_LVL_2 = []
NAVIGATION_LVL_6 = []