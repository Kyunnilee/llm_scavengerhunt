# LLMSacavengerHunt
A New Benchmark made for tasks for Large Language Model Agents - UC Berkeley Scavenger Hunt

## Explanation of Our Directories

`./`: our main directory, mainly for our code implementation of LLMScavengerHunt  
`output/`: our generate data (e.g. google street view's generated image, 
googleapi's generated nodes & maps, etc.)  
`updates/`: our update info (if you need to tell others what your commit is about, write it here!)  
`util/`: our utility functions (e.g. visualizing maps with interactive html, poe/openai/autogen backend, etc.)  
`touchdown/`: [Touchdown](https://arxiv.org/abs/1811.12354#)'s code implementation and dataset  

## For 10/31 meeting
1. Set up poe config(`./config/poe_test_navi.json`), ref [peo-api-wrapper](https://github.com/snowby666/poe-api-wrapper?tab=readme-ov-file#models)
2. Map related `./config/map_config.py`
3. Init prompt `./config/poe_test_navi.json`, `policy`
4. Prompt to trigger agent to ask question `./config/human_test_oracle.json`, `question`
5. Instruction at each step `poe_navigator.py`, in func `get_navigation_instruction`