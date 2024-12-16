# -*- coding:utf-8 -*-

from graph_loader import *
from typing import *

import os
import json
import googlemaps
import time

turn_around_angle_limit = 60
forward_angle_limit = 90

FORWARD_RANGE = range(0, int(forward_angle_limit/2))
TURN_AROUND_RANGE = range(0, int(turn_around_angle_limit/2 + 1))
LEFT_RIGHT_RANGE = range(int(forward_angle_limit/2), int(180-turn_around_angle_limit/2))


class BaseNavigator:
    def __init__(self, task_config:dict, map_config:dict):
        self.graph: Graph = GraphLoader(map_config).construct_graph()
        self.graph_state: Tuple[str, int] = None # Tuple[curr_panoid, curr_heading]
        self.prev_graph_state = None
        
        self.task_config = task_config
        self.start_node: str = task_config["start_node"]
        # self.max_steps: int = task_config["max_steps"]
        self.max_step: int = 150 # tmp, for 12/12 testing 
        
        # Assume we have only one target now, hence len(list)==1
        self.target_infos: List[Dict[str, str]] = task_config["target_infos"] # key: panoid, status, ...
        for info in self.target_infos:
            info["status"] = False
        self.arrive_threshold: int = task_config["arrive_threshold"]

    def navigate(self):
        raise NotImplementedError

    def step(self, action):
        '''
        Execute one step and update the state. 
        go_towards: ['forward', 'left', 'right', 'turn_around', 'stop']
        '''
        if action == 'stop':
            arrive, info = self.check_arrival()
            if arrive:
                return f'Arrived at target {info["name"]}, place: {info["panoid"]}.'
            else:
                return "Not arrived yet. Can't choose stop. Maybe you are not close enough to destination."
        
        available_actions, _ = self.get_available_next_moves(self.graph_state)
        if action not in available_actions:
            # print(f'Invalid action: {go_towards}.')
            return f'Invalid action: {action}.'
        
        next_panoid, next_heading = self._get_next_graph_state(self.graph_state, action)
        if len(self.graph.nodes[next_panoid].neighbors) < 2:
            # stay still when running into the boundary of the graph
            # print(f'At the border (number of neighbors < 2). Did not go "{go_towards}".')
            return f'At the border (number of neighbors < 2). Did not go "{action}".'
        self.prev_graph_state = self.graph_state
        self.graph_state = (next_panoid, next_heading)
        return ""
        
    def _get_next_graph_state(self, curr_state, go_towards):
        '''Get next state without changing the current state.'''
        curr_panoid, curr_heading = curr_state

        if go_towards == 'forward':
            neighbors = self.graph.nodes[curr_panoid].neighbors
            if curr_heading in neighbors:
                # use current heading to point to the next node
                next_node = neighbors[curr_heading]
            else:
                # weird node, stay put
                next_node = self.graph.nodes[curr_panoid]
        elif go_towards == 'left' or go_towards == 'right' or go_towards == 'turn_around':
            # if turn left or right, stay at the same node 
            next_node = self.graph.nodes[curr_panoid]
        else:
            raise ValueError('Invalid action.')

        next_panoid = next_node.panoid
        next_heading = self._get_nearest_heading(curr_state, next_node, go_towards) # if not forward, next_node is the same node
        return next_panoid, next_heading
    
    def _check_action_validity(self, curr_state, go_towards):
        '''
        check [forward, left, right, turn_around] action validity. 
        If there is node in the limit range, return True.
        assume forward action is always valid.
        '''
        curr_panoid, curr_heading = curr_state
        current_node = self.graph.nodes[curr_panoid]
        _, diff = self._get_nearest_heading_and_diff(curr_state, current_node, go_towards)
        if go_towards == 'forward':
            return diff in FORWARD_RANGE
        elif go_towards == 'turn_around':
            return diff in TURN_AROUND_RANGE
        elif go_towards == 'left' or go_towards == 'right':
            return diff in LEFT_RIGHT_RANGE or diff in range(1, int(forward_angle_limit/2))
        else:
            raise ValueError('Invalid action or try to check forward action.')
        
    def _get_diff_func(self, go_towards):
        if go_towards == 'forward':
            diff_func = lambda next_heading, curr_heading: 180 - abs(abs(next_heading - curr_heading) - 180)
        elif go_towards == 'left':
            diff_func = lambda next_heading, curr_heading: (curr_heading - next_heading) % 360
        elif go_towards == 'right':
            diff_func = lambda next_heading, curr_heading: (next_heading - curr_heading) % 360
        elif go_towards == 'turn_around':
            def diff_func(next_heading, curr_heading):
                if curr_heading < 0:
                    curr_heading += 180
                else:
                    curr_heading -= 180
                return 180 - abs(abs(next_heading - curr_heading) - 180)
            return diff_func
        else:
            raise ValueError('Invalid action.')
        return diff_func
        
    def _get_nearest_heading(self, curr_state, next_node, go_towards, start=False):
        _, curr_heading = curr_state
        next_heading = None

        diff = float('inf')
        diff_func = self._get_diff_func(go_towards)

        for heading in next_node.neighbors.keys(): # next node could be same as current node, or next node (forward)
            if heading == curr_heading and go_towards != 'forward':
                # don't match to the current heading when turning
                continue
            
            diff_ = diff_func(int(heading), int(curr_heading))
            
            if not start and go_towards == 'forward' and diff_ not in FORWARD_RANGE:
                # don't automatical turn to nearest heading if no proper neighbor
                continue
            
            if diff_ < diff:
                diff = diff_
                next_heading = heading

        if next_heading is None:
            next_heading = curr_heading
        return int(next_heading)
    
    def _get_nearest_heading_and_diff(self, curr_state, current_node, go_towards): # get diff to validate action
        _, curr_heading = curr_state
        next_heading = None

        diff = float('inf')
        diff_func = self._get_diff_func(go_towards)

        for heading in current_node.neighbors.keys(): # next node could be same as current node, or next node (forward)
            if heading == curr_heading and go_towards != 'forward':
                # don't match to the current heading when turning
                continue
            
            diff_ = diff_func(int(heading), int(curr_heading))
            
            if diff_ < diff:
                diff = diff_
                next_heading = heading

        if next_heading is None:
            next_heading = curr_heading
        return int(next_heading), diff
    
    def fix_heading(self, curr_state):
        '''Fix the heading of the current state based on the pano_yaw_angle of the current node.'''
        panoid, heading = curr_state
        curr_node = self.graph.nodes[panoid]
        new_heading = self._get_nearest_heading(curr_state, curr_node, 'forward', start=True)
        return panoid, new_heading

    def get_available_next_moves(self, graph_state):
        '''Given current node, get available next actions and states.'''
        next_actions = ['forward', 'left', 'right', 'turn_around']
        available_actions = []
        available_next_states = []
        for action in next_actions:
            if self._check_action_validity(graph_state, action):
                available_actions.append(action)
                available_next_states.append(self._get_next_graph_state(graph_state, action))
            
        return available_actions, available_next_states

    def _get_action_between_nodes(self, panoid_from: str, panoid_to: str, 
                                        curr_heading: int):
        '''
        Assumes curr_heading is heading towards some neighbouring node.
        Assumes that node_from and node_to are NEIGHBOURING
        Calculates what's the action to go from node_from to node_to.
        '''
        neighbor_panoids = [node.panoid for node in \
                            self.graph.nodes[panoid_from].neighbors.values()]
        if panoid_to not in neighbor_panoids:
            raise ValueError(f"Target node {panoid_to} is not neighbour of {panoid_from}.")
        
        for neighbor_heading, neighbor_node in self.graph.nodes[panoid_from].neighbors.items():
            if neighbor_node.panoid == panoid_to:
                target_heading = neighbor_heading

        # if heading is node_to, return FORWARD
        if curr_heading == target_heading:
            return ["forward"]

        # if in left LEFT_RIGHT_RANGE°, return turn_left * N + forward
        left_func = self._get_diff_func("left")
        turn_left_angle = left_func(curr_heading=curr_heading, next_heading=target_heading)
        if turn_left_angle in LEFT_RIGHT_RANGE or turn_left_angle in range(1, int(forward_angle_limit/2)):
            turn_left_cnt = 1
            for heading in self.graph.nodes[panoid_from].neighbors.keys():
                if 0 < left_func(curr_heading=curr_heading, next_heading=heading) < turn_left_angle:
                    turn_left_cnt += 1
            return ["left" for _ in range(turn_left_cnt)] + ["forward"]

        # if in right LEFT_RIGHT_RANGE°, return turn_left * N + forward
        right_func = self._get_diff_func("right")
        turn_right_angle = right_func(curr_heading=curr_heading, next_heading=target_heading)
        if turn_right_angle in LEFT_RIGHT_RANGE or turn_right_angle in range(1, int(forward_angle_limit/2)):
            turn_right_cnt = 1
            for heading in self.graph.nodes[panoid_from].neighbors.keys():
                if 0 < right_func(curr_heading=curr_heading, next_heading=heading) < turn_right_angle:
                    turn_right_cnt += 1
            return ["right" for _ in range(turn_right_cnt)] + ["forward"]

        # if in left back or right back, turn around first then do the same as above
        # print(f"before: {curr_heading}")
        _, curr_heading = self._get_next_graph_state(
            (panoid_from, curr_heading), "turn_around"
        )
        # print("turn around to", curr_heading)

        if curr_heading == target_heading:
            return ["turn_around", "forward"]

        # if in left 1-90°, return turn_left * N + forward
        left_func = self._get_diff_func("left")
        turn_left_angle = left_func(curr_heading=curr_heading, next_heading=target_heading)
        if turn_left_angle in TURN_AROUND_RANGE:
            turn_left_cnt = 1
            for heading in self.graph.nodes[panoid_from].neighbors.keys():
                if 0 < left_func(curr_heading=curr_heading, next_heading=heading) < turn_left_angle:
                    turn_left_cnt += 1
            return ["turn_around"] + \
                    ["left" for _ in range(turn_left_cnt)] + \
                    ["forward"]

        # if in right 0-90°, return turn_left * N + forward
        right_func = self._get_diff_func("right")
        turn_right_angle = right_func(curr_heading=curr_heading, next_heading=target_heading)
        if turn_right_angle in TURN_AROUND_RANGE:
            turn_right_cnt = 1
            for heading in self.graph.nodes[panoid_from].neighbors.keys():
                if 0 < right_func(curr_heading=curr_heading, next_heading=heading) < turn_right_angle:
                    turn_right_cnt += 1
            return ["turn_around"] + \
                    ["right" for _ in range(turn_right_cnt)] + \
                    ["forward"]
        
        raise ValueError(f"Cant calculate action from node {panoid_from} to {panoid_to}")

    def _get_correct_action_sequence(self, node_from, node_to, init_heading):
        """
        Gets action sequence from given path.
        Returns: List[str], List of actions.
        """
        # Get the path between nodes
        path = self.graph.get_path(node_from=node_from, node_to=node_to)

        if len(path) <= 1:
            return ["No action needed. You have arrived."]

        action_list = []
        curr_heading = init_heading
        for idx in range(len(path) - 1):
            curr_action_list = self._get_action_between_nodes(
                panoid_from=path[idx], panoid_to=path[idx+1], curr_heading=curr_heading, 
            )

            for action in curr_action_list:
                _, curr_heading = self._get_next_graph_state(
                    curr_state=(path[idx], curr_heading), go_towards=action
                )

            action_list += curr_action_list
        
        return action_list, path

    def _query_clue(self, lat: float, lng: float, 
                            info_type: str, overwrite_radius: int = None) -> Dict:
        """
        Get specific information about a location.
        
        Args:
            lat: Latitude
            lng: Longitude
            info_type: Type of information wanted 
                ('street' | 'neighbors' | 'landmarks' | 'attractions' | 'subway')
        
        Returns:
            Dictionary containing requested information
        """
        try:
            google_api_key = os.environ.get("GOOGLE_API_KEY")
            if google_api_key is None:
                raise ValueError("Your GOOGLE_API_KEY is None. Check if it is in your environment. If it is, try restart computer.")
            gmaps = googlemaps.Client(key=google_api_key)
            
            if info_type == 'street':
                result = gmaps.reverse_geocode((lat, lng))
                if result:
                    # iter through all streets
                    for component in result[0]['address_components']:
                        if 'route' in component['types']:
                            return {"street": component['long_name']}
                    # if type route not found, return sublocality
                    for component in result[0]['address_components']:
                        if 'sublocality' in component['types']:
                            return {"street": component['long_name']}
                return {"street": "Unknown street"}
                
            elif info_type == 'neighbors':
                result = gmaps.places_nearby(
                    location=(lat, lng),
                    radius=20 if overwrite_radius is None else overwrite_radius,  # 20m radius
                    type='premise',
                    # rank_by='distance'
                )
                
                if not result.get('results'):
                    return {"neighbors": "No buildings found"}
                
                nearest = result['results'][0]
                return {"neighbors": {
                    "name": nearest['name'],
                    "address": nearest.get('vicinity', 'No address'),
                    "type": nearest.get('types', ['unknown'])[0]
                }}
                
            elif info_type == 'landmarks':
                result = gmaps.places_nearby(
                    location=(lat, lng),
                    radius=50 if overwrite_radius is None else overwrite_radius,  # 50m radius
                    type='point_of_interest', 
                    # rank_by='distance'
                )
                
                if not result.get('results'):
                    return {"landmarks": "No landmarks found"}
                    
                landmarks = []
                for place in result['results'][:3]: # ONLY use the first 3
                    landmarks.append({
                        "name": place['name'],
                        "address": place.get('vicinity', 'No address')
                    })
                return {"landmarks": landmarks}
                
            elif info_type == 'attractions':
                result = gmaps.places_nearby(
                    location=(lat, lng),
                    radius=50 if overwrite_radius is None else overwrite_radius,
                    type='tourist_attraction', 
                    # rank_by='distance'
                )
                
                if not result.get('results'):
                    return {"attractions": "No attractions found"}
                    
                attractions = []
                for place in result['results'][:3]:
                    attractions.append({
                        "name": place['name'],
                        "address": place.get('vicinity', 'No address')
                    })
                return {"attractions": attractions}

            elif info_type == 'subway':
                # Query for nearby subway stations (type = 'subway_station')
                result = gmaps.places_nearby(
                    location=(lat, lng),
                    radius=10 if overwrite_radius is None else overwrite_radius,  # 500m radius to find nearby subway stations
                    type='subway_station',
                    # rank_by='distance'
                )
                
                if not result.get('results'):
                    return {"subway": "No subway stations found"}
                
                nearest_subway = result['results'][0]
                return {"subway": {
                    "name": nearest_subway['name'],
                    "address": nearest_subway.get('vicinity', 'No address')
                }}
                
            else:
                return {"error": "Unknown info_type"}
                
        except Exception as e:
            return {"error": f"Failed to get information: {str(e)}"}
    
    def _query_batch_func(self, panoids: List[str], info_type) -> Callable:
        """
        info_type: 
        + Type of information wanted 
        + ('street' | 'neighbors' | 'landmarks' | 'attractions' | 'subway')
        """
        def __func():
            results = []
            for panoid in panoids:
                if len(panoid) > 15:
                    time.sleep(0.2)
                coord = self.graph.nodes[panoid].coordinate
                results.append(
                    self._query_clue(coord[0], coord[1], info_type)
                )
            return results

        return __func

    def check_arrival(self):
        '''
        Check if the navigator has arrived at the target node.
        '''
        lat, lng = self.graph.nodes[self.graph_state[0]].coordinate
        for info in self.target_infos:
            if info["status"]:
                continue
            target_lat, target_lng = self.graph.nodes[info["panoid"]].coordinate
            distance = haversine(
                coord1=(lat, lng), 
                coord2=(target_lat, target_lng)
            ) # This is distance (unit: meters) between curr and target
            
            if distance < self.arrive_threshold:
                info["status"] = True
                return True, info
        
        return False, None
    
    def check_arrival_all(self):
        '''
        Check if the navigator has arrived at all target nodes.
        '''
        for info in self.target_infos:
            if not info["status"]:
                return False
        return True
    
    def collect_arrival_info(self):
        '''
        Collect the arrival information of the navigator.
        '''
        arrival_info = []
        for info in self.target_infos:
            arrival_info.append({"name": info["name"], "panoid": info["panoid"], "status": info["status"]})
        return arrival_info

    def collect_persistent_observations(self):
        '''
        Collect all related world states as input of QA agent
        '''
        clues: Dict[str, Any] = {}

        target_panoid = self.target_infos[0]["panoid"]  
        target_coord = self.graph.nodes[target_panoid].coordinate

        # 1. add target location clues
        try:
            res = self._query_clue(target_coord[0], target_coord[1], "landmarks")
            clues["target_nearby_landmarks"] = res["landmarks"]

            res = self._query_clue(target_coord[0], target_coord[1], "attractions")
            clues["target_nearby_attractions"] = res["attractions"]

            res = self._query_clue(target_coord[0], target_coord[1], "neighbors")
            clues["target_nearby_neighbors"] = res["neighbors"]

            res = self._query_clue(target_coord[0], target_coord[1], "street")
            clues["target_street"] = res["street"]
        
        except Exception as e:
            print(res)
            print(f"Query failed.")
            raise e
        
        return clues


    def collect_observations(self):
        '''
        Collect all related world states as input of QA agent
        '''
        world_states: Dict[str, Any] = {}
        clues: Dict[str, Any] = {}

        curr_panoid, curr_heading = self.graph_state
        target_panoid = self.target_infos[0]["panoid"]  
        curr_coord = self.graph.nodes[curr_panoid].coordinate
        target_coord = self.graph.nodes[target_panoid].coordinate

        # 1. collect correct path from curr to target
        #    *Assume we have only one target now
        world_states["path_action"], world_states["path_nodes"] = \
            self._get_correct_action_sequence(
                node_from=curr_panoid, 
                node_to=target_panoid, 
                init_heading=curr_heading, 
            )
        world_states["path_streets"] = self._query_batch_func(world_states["path_nodes"], info_type="street")
        world_states["path_subways"] = self._query_batch_func(world_states["path_nodes"], info_type="subway")
        world_states["path_len"] = len(world_states["path_nodes"])

        # 2. collect global location of curr and target
        world_states["abs_curr_pos"] = curr_coord
        world_states["abs_target_pos"] = target_coord
        world_states["abs_euclidean_dist"] = haversine(curr_coord, target_coord)
        world_states["abs_curr_dir"] = self.graph.get_abs_direction(curr_coord)
        world_states["abs_target_dir"] = self.graph.get_abs_direction(target_coord)

        # 3. collect relative location of target and curr
        world_states["rel_target_pos"] = get_rel_direction(
            curr_coord=curr_coord, 
            target_coord=target_coord, 
            heading=curr_heading, 
        )
        world_states["rel_curr_pos"] = get_rel_direction(
            curr_coord=target_coord, 
            target_coord=curr_coord, 
            heading=curr_heading, 
        )

        # 4. add target information
        world_states["target_name"] = self.target_infos[0]["name"]

        # 1. add current location clues
        try:
            res = self._query_clue(curr_coord[0], curr_coord[1], "landmarks")
            clues["curr_nearby_landmarks"] = res["landmarks"]

            res = self._query_clue(curr_coord[0], curr_coord[1], "attractions")
            clues["curr_nearby_attractions"] = res["attractions"]

            res = self._query_clue(curr_coord[0], curr_coord[1], "neighbors")
            clues["curr_nearby_neighbors"] = res["neighbors"]

            res = self._query_clue(curr_coord[0], curr_coord[1], "street")
            clues["curr_street"] = res["street"]
        
        except Exception as e:
            print(res)
            print(f"Query failed.")
            raise e
        
        return world_states, clues

    def show_state_info(self, graph_state):
        '''Given a graph state, show current state information and available next moves.'''
        message = ''
        available_actions, next_graph_states = self.get_available_next_moves(graph_state)
        for action, next_graph_state in zip(available_actions, next_graph_states):
            if action == 'forward':
                # message += f'\n[Action: {action}], go to: {self.graph.get_node_coordinates(next_graph_state[0])}, heading: {next_graph_state[1]}'
                message += f'\n[Action: {action}], go to new position in front of you.'
                
            else:
                # message += f'\n[Action: {action}], heading: {next_graph_state[1]}'
                message += f'\n[Action: {action}], turn to new direction in the same position.'
        return message
        
    def get_state_edges(self, graph_state):
        '''Given a graph state, return the edges of the current node.'''
        panoid, heading = graph_state
        edges = self.graph.nodes[panoid].neighbors
        message = f'Edges of node {panoid}:'
        for heading, node in edges.items():
            message += f'\nHeading: {heading}, node: {node.panoid}, lat: {node.coordinate[0]}, lng: {node.coordinate[1]}'
        return message

if __name__ == "__main__":
    with open("config/task/example_touchdown_task.json", "r") as f:
        tsk_cfg = json.load(f)
    with open("config/map/touchdown_streetmap.json", "r") as f:
        map_cfg = json.load(f)
    test_nav = BaseNavigator(task_config=tsk_cfg, map_config=map_cfg)

    res = test_nav._query_clue(37.877530, -122.262665, "street")
    print(res)

    # test_panoid_start = "65352337"
    # test_panoid_to = [node.panoid for node in \
    #                   test_nav.graph.nodes[test_panoid_start].neighbors.values()]
    # test_panoid_start_heading = list(test_nav.graph.nodes[test_panoid_start].neighbors.keys())

    # print(test_panoid_start)
    # print(test_panoid_to)
    # print(test_panoid_start_heading)

    # for idx, target in enumerate(test_panoid_to):
    #     for heading in test_panoid_start_heading:
    #         result = test_nav._get_action_between_nodes(
    #             panoid_from=test_panoid_start, 
    #             panoid_to=target, 
    #             curr_heading=heading
    #         )
    #         print(f"Config: target={target}, init_heading={heading}, target_heading={test_panoid_start_heading[idx]}")
    #         print(f"Result: {result}")

    # test_panoid_start = "6639218292"
    # test_panoid_end = "5434001267"
    # test_panoid_start_heading = list(test_nav.graph.nodes[test_panoid_start].neighbors.keys())
    # print(test_panoid_start_heading)

    # test_path = test_nav._get_correct_action_sequence(
    #     node_from=test_panoid_start, 
    #     node_to=test_panoid_end, 
    #     init_heading=168
    # )
    # print(test_path) 
