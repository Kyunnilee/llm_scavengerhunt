import importlib
import os

dependencies = [
    'requests',
    'PIL',
    'openai',
    'tqdm',
    'json',
    'googlemaps',
    'time',
    'typing',
    'math',
    'collections',
    're',
    'argparse',
    'tempfile',
    'anthropic',
    'base64',
    'google.generativeai',
    'io',
    'mistralai',
]

api_keys = [
    'OPENAI_API_KEY',
    'GOOGLE_API_KEY',
    'ANTHROPIC_API_KEY',
    'MISTRAL_API_KEY'
]

def check_dependencies(dependencies):
    missing_dependencies = []
    for dependency in dependencies:
        try:
            importlib.import_module(dependency)
        except ImportError:
            missing_dependencies.append(dependency)
    return missing_dependencies

def check_api_keys(api_keys):
    missing_keys = []
    for key in api_keys:
        if not os.environ.get(key):
            missing_keys.append(key)
    return missing_keys

if __name__ == "__main__":
    print("Checking dependencies...")
    missing_dependencies = check_dependencies(dependencies)
    if missing_dependencies:
        print(f"Missing dependencies: {', '.join(missing_dependencies)}")
    else:
        print("All dependencies are installed.")

    print("\nChecking API keys...")
    missing_keys = check_api_keys(api_keys)
    if missing_keys:
        print(f"Missing API keys: {', '.join(missing_keys)}")
    else:
        print("All API keys are set.")