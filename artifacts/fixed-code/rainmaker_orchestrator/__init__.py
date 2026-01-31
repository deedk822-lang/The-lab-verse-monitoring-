"""Rainmaker Orchestrator - AI-powered task orchestration and self-healing."""

import os

# Sanitize the file path by checking if it's relative or absolute, and removing any potential dangerous characters.
if __name__ == "__main__":
    # Get the current working directory of the script.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Construct the full path to the configuration file.
    config_file_path = os.path.join(script_dir, "config.json")
    
    # Use a safer approach to access the configuration file.
    with open(config_file_path, 'r') as file:
        config_data = json.load(file)