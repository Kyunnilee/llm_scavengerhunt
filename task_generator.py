import json
import os
from typing import Dict, Any

def read_source_json(input_file: str = "output/possible_starts.json") -> Dict[str, Any]:
    """Read the source JSON file."""
    with open(input_file, 'r') as f:
        return json.load(f)

def generate_task_jsons(source_data: Dict[str, Any], output_dir: str = "output/tasks"):
    """
    Generate individual task JSON files for each start point.
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract target information
    target_location = source_data["target_location"]
    target_nodes = source_data["target_nodes"]
    
    # Create target_infos with combined information and actual landmark name
    target_infos = []
    for target_node in target_nodes:
        target_info = {
            "panoid": target_node["node_id"],
            "name": target_location["name"],  # Use actual landmark name
            "latitude": target_location["latitude"],
            "longitude": target_location["longitude"],
            "address": target_location["address"],
            "description": target_location["description"]
        }
        target_infos.append(target_info)

    # Generate individual JSON files for each start point
    for start_point in source_data["start_points"]:
        task_data = {
            "start_node": start_point["node_id"],
            "start_heading": 0,
            "target_infos": target_infos,
            "arrive_threshold": 25
        }
        
        # Create filename using start node ID
        filename = f"task_{start_point['node_id']}.json"
        filepath = os.path.join(output_dir, filename)
        
        # Write the JSON file
        with open(filepath, 'w') as f:
            json.dump(task_data, f, indent=4)
        
        print(f"Generated task file: {filename}")

def main():
    # Read the source JSON
    source_data = read_source_json()
    
    # Generate task JSONs
    generate_task_jsons(source_data)
    
    print("\nTask generation completed!")
    print(f"Generated {len(source_data['start_points'])} task files")

if __name__ == "__main__":
    main()