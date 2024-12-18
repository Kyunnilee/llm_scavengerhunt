import os
import subprocess

if __name__ == "__main__":
    cmd = "python navigator.py --navi=mistralai_pixtral-12b-2409_navi.json "
    cmd += "--map=touchdown_streetmap.json "
    cmd += "--eval=evaluator.json "
    cmd += "--task=<<<task_placeholder>>> "
    cmd += "--vision=openai_vision.json "

    task_dir = os.path.join("config", "task", "1215_experiment_1")
    
    for task_name in os.listdir(task_dir):
        for _ in range(4):
            task_relative_path = os.path.join("1215_experiment_1", task_name)
            print(f"\n\n======================\nRunning {task_name}\n======================")
            task_cmd = cmd.replace("<<<task_placeholder>>>", task_relative_path)
            result = subprocess.run(task_cmd, shell=True, capture_output=True, text=True)
            
            print("Output:")
            print(result.stdout)
            print("Error:")
            print(result.stderr)

            if result.returncode != 0:
                print(f"Error occurred while running {task_name}.")
