import os
from graph_loader import GraphLoader, Graph

turn_around_angle_limit = 60
forward_angle_limit = 90
TURN_AROUND_RANGE = range(int(180-turn_around_angle_limit/2), 180+1)
FORWARD_RANGE = range(0, int(forward_angle_limit/2))
LEFT_RIGHT_RANGE = range(int(forward_angle_limit/2), int(180-turn_around_angle_limit/2)+1)

class BaseNavigator:
    def __init__(self, cfg: dict=None):
        if cfg is None:
            self.graph: Graph = GraphLoader().construct_graph()
        else:
            self.graph: Graph = GraphLoader(cfg).construct_graph()

        self.graph_state = None # Tuple[curr_panoid, curr_heading]
        self.prev_graph_state = None

    def navigate(self):
        raise NotImplementedError

    def step(self, go_towards):
        '''
        Execute one step and update the state. 
        go_towards: ['forward', 'left', 'right', 'turn_around']
        '''
        available_actions, _ = self.get_available_next_moves(self.graph_state)
        if go_towards not in available_actions:
            # print(f'Invalid action: {go_towards}.')
            return f'Invalid action: {go_towards}.'
        
        next_panoid, next_heading = self._get_next_graph_state(self.graph_state, go_towards)
        if len(self.graph.nodes[next_panoid].neighbors) < 2:
            # stay still when running into the boundary of the graph
            # print(f'At the border (number of neighbors < 2). Did not go "{go_towards}".')
            return f'At the border (number of neighbors < 2). Did not go "{go_towards}".'
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
        next_heading = self._get_nearest_heading(curr_state, next_node, go_towards)
        return next_panoid, next_heading
    
    def _check_action_validity(self, curr_state, go_towards):
        '''
        check [left, right, turn_around] action validity. 
        If there is node in the limit range, return True.
        assume forward action is always valid.
        '''
        curr_panoid, curr_heading = curr_state
        current_node = self.graph.nodes[curr_panoid]
        _, diff = self._get_nearest_heading_and_diff(curr_state, current_node, go_towards, inplace=True)
        if go_towards == 'forward':
            return diff in FORWARD_RANGE
        elif go_towards == 'turn_around':
            return diff in TURN_AROUND_RANGE
        elif go_towards == 'left' or go_towards == 'right':
            return diff in LEFT_RIGHT_RANGE
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
            diff_func = lambda next_heading, curr_heading: 180 - abs(abs(next_heading - curr_heading) - 180)
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
    
    def _get_nearest_heading_and_diff(self, curr_state, next_node, go_towards, inplace=False):
        _, curr_heading = curr_state
        next_heading = None

        diff = float('inf')
        diff_func = self._get_diff_func(go_towards)

        for heading in next_node.neighbors.keys(): # next node could be same as current node, or next node (forward)
            if heading == curr_heading and go_towards != 'forward':
                # don't match to the current heading when turning
                continue
            
            diff_ = diff_func(int(heading), int(curr_heading))
            
            if go_towards == 'forward' and not inplace and diff_ not in FORWARD_RANGE:
                # don't automatical turn to nearest heading if no proper neighbor
                continue
            
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
            if action == 'forward':
                if self._check_action_validity(graph_state, action):
                    available_actions.append(action)
                    available_next_states.append(self._get_next_graph_state(graph_state, action))
            elif action == 'left' or action == 'right' or action == 'turn_around':
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
        print(f"before: {curr_heading}")
        _, curr_heading = self._get_next_graph_state(
            (panoid_from, curr_heading), "turn_around"
        )
        print("turn around to", curr_heading)

        # if in left 1-90°, return turn_left * N + forward
        left_func = self._get_diff_func("left")
        turn_left_angle = left_func(curr_heading=curr_heading, next_heading=target_heading)
        if turn_left_angle in LEFT_RIGHT_RANGE or turn_left_angle in range(1, int(forward_angle_limit/2)):
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
        if turn_right_angle in LEFT_RIGHT_RANGE or turn_right_angle in range(1, int(forward_angle_limit/2)):
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

        Returns: List of (action, next_node) pairs. Each next_node is a str of panoid.
        Example:
                [(None, node_start), 
                ("forward", node_1), 
                ("right", node_2), ...]
        """
        # Get the path between nodes
        path = self.graph.get_path(node_from=node_from, node_to=node_to)

        if not path:
            raise ValueError(f"No path found between {node_from} and {node_to}.")

        # Init action sequence
        action_sequence = [(None, path[0])]

        for i in range(len(path) - 1):
            current_node = self.graph.nodes[path[i]]
            next_node = self.graph.nodes[path[i + 1]]
            
            # Calc current heading
            if i == 0:
                current_heading = init_heading
            else:
                # Find heading to reach the current node from the previous node
                prev_node = self.graph.nodes[path[i - 1]]
                for heading, neighbor in prev_node.neighbors.items():
                    if neighbor.panoid == current_node.panoid:
                        current_heading = heading
                        break
                else:
                    raise ValueError(f"Could not determine heading from {prev_node.panoid} to {current_node.panoid}.")
            
            # Find the heading from current_node to next_node
            for heading, neighbor in current_node.neighbors.items():
                if neighbor.panoid == next_node.panoid:
                    next_heading = heading
                    break
            else:
                raise ValueError(f"Could not determine heading from {current_node.panoid} to {next_node.panoid}.")

            # Calc action based on the heading difference
            diff = int((next_heading - current_heading) % 360)
            print(f"at node {action_sequence[-1][1]}, diff={diff}")
            if diff in TURN_AROUND_RANGE:
                action = "turn_around"
            elif diff in LEFT_RIGHT_RANGE:
                if diff < 180:
                    action = "right"
                else:
                    action = "left"
            else:
                action = "forward"

            action_sequence.append((action, next_node.panoid))

        return action_sequence

    def collect_world_state(self):
        '''
        Collect all related world states as input of QA agent
        '''

        # 1. collect correct path from curr to target

        # 2. collect global location of curr and target

        # 3. collect relative location of target (surroundings)

        # 4. collect relative location of curr (surroundings)



    def show_state_info(self, graph_state):
        '''Given a graph state, show current state information and available next moves.'''
        message = 'Current graph state: {}'.format(graph_state)
        # print('Current graph state: {}'.format(graph_state))
        available_actions, next_graph_states = self.get_available_next_moves(graph_state)

        # print('Available next actions and graph states:')
        message += '\nAvailable next actions and graph states:'
        for action, next_graph_state in zip(available_actions, next_graph_states):
            # print('Action: {}, to graph state: {}'.format(action, next_graph_state))
            if action == 'forward':
                message += f'\nAction: {action}, to graph state: {next_graph_state}'
            else:
                message += f'\nAction: {action}, heading: {next_graph_state[1]}'
        # print('==============================')
        # print(message)
        return message
        
    def get_state_edges(self, graph_state):
        '''Given a graph state, return the edges of the current node.'''
        panoid, heading = graph_state
        edges = self.graph.nodes[panoid].neighbors
        message = f'Edges of node {panoid}:'
        for heading, node in edges.items():
            message += f'\nHeading: {heading}, node: {node.panoid}, lat: {node.coordinate[0]}, lng: {node.coordinate[1]}'
        # print(message)
        return message

if __name__ == "__main__":
    test_nav = BaseNavigator()

    test_panoid_start = "65352337"
    test_panoid_to = [node.panoid for node in \
                      test_nav.graph.nodes[test_panoid_start].neighbors.values()]
    test_panoid_start_heading = list(test_nav.graph.nodes[test_panoid_start].neighbors.keys())

    print(test_panoid_start)
    print(test_panoid_to)
    print(test_panoid_start_heading)

    for idx, target in enumerate(test_panoid_to):
        for heading in test_panoid_start_heading:
            result = test_nav._get_action_between_nodes(
                panoid_from=test_panoid_start, 
                panoid_to=target, 
                curr_heading=heading
            )
            print(f"Config: target={target}, init_heading={heading}, target_heading={test_panoid_start_heading[idx]}")
            print(f"Result: {result}")



    # test_path = test_nav._get_correct_action_sequence(
    #     node_from="6958214919", node_to="370202538", init_heading=82
    # )
    # print(test_path) 
