import os
import sys
from qwen_agent.agents import Assistant
# Ensure we can import tools
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from src.tools.github_ops import GitHubOmniscience

class MasterController:
    def __init__(self):
        self.api_key = os.getenv("DASHSCOPE_API_KEY")

        self.sysadmin = Assistant(
            llm={'model': 'qwen-max'},
            name='Qwen System Admin',
            description='Autonomous Engineer. Fixes bugs.',
            function_list=['github_omniscience']
        )

    def heal_from_file(self, log_file_path):
        """
        ROBUST METHOD: Reads the error log file directly from disk.
        """
        if not os.path.exists(log_file_path):
            return "Error: Log file not found."

        try:
            with open(log_file_path, 'r') as f:
                error_content = f.read()
        except Exception as e:
            return f"Error reading log: {e}"

        print(f"🚨 QWEN: Analyzing crash log ({len(error_content)} chars)...")

        prompt = f"""
        CRITICAL FAILURE DETECTED.

        ERROR LOG:
        {error_content[:5000]} # Truncate to fit context if massive

        MISSION:
        Analyze the traceback. Use 'github_omniscience' to locate the failing file and propose a fix.
        """

        response = self.sysadmin.run(messages=[{'role': 'user', 'content': prompt}])

        solution = ""
        for chunk in response:
            solution += chunk.get('content', '')

        return solution

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("logfile", help="Path to the crash log")
    args = parser.parse_args()

    admin = MasterController()
    print(admin.heal_from_file(args.logfile))
