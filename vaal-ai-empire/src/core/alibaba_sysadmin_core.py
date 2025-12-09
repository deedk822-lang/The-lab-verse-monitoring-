import os
import sys
import logging
from qwen_agent.agents import Assistant

# Dynamic Path Setup
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

try:
    from src.tools.github_ops import GitHubOmniscience
except ImportError:
    GitHubOmniscience = None

logger = logging.getLogger("SysAdminCore")
logging.basicConfig(level=logging.INFO)

class MasterController:
    def __init__(self):
        # 1. Validate Brain Keys
        self.api_key = os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY missing.")

        # 2. Validate Hands Keys (The PAT)
        self.github_token = os.getenv("PERSONAL_ACCESS_TOKEN")
        if not self.github_token:
            logger.warning("⚠️ PERSONAL_ACCESS_TOKEN missing. Qwen cannot fix code.")

        # The Automated Security Engineer
        self.sysadmin = Assistant(
            llm={'model': 'qwen-max'},
            name='Qwen Security Engineer',
            description='Automated Security Patcher.',
            system_message="""
            You are the Chief Security Officer (CSO) AI.

            YOUR MISSION:
            1. Analyze security alerts provided by 'prod_security_analyzer'.
            2. Locate the vulnerable code using 'github_omniscience' (list_files).
            3. Read the file content.
            4. REWRITE the code to fix the vulnerability (e.g., remove hardcoded keys, close ports).
            5. Commit the fix using 'github_omniscience' (update_file).

            PROTOCOL:
            - Never break functionality.
            - Always use environment variables (os.getenv) for secrets.
            - Add comments explaining the security fix.
            """,
            function_list=['github_omniscience']
        )

    def patch_security_vulnerability(self, risk_report):
        """
        Input: A report from prod_security_analyzer
        """
        if not self.github_token:
            return "❌ Cannot Patch: GitHub Token missing in environment."

        logger.info(f"🚨 SECURITY ALERT RECEIVED: {risk_report}")

        prompt = f"""
        SECURITY VULNERABILITY DETECTED.
        DETAILS:
        {risk_report}

        INSTRUCTION:
        Find the file, fix the issue by using environment variables, and commit the patch.
        """

        # Run Qwen Loop
        response = self.sysadmin.run(messages=[{'role': 'user', 'content': prompt}])

        result = ""
        for chunk in response:
            result += chunk.get('content', '')
        return result

if __name__ == "__main__":
    admin = MasterController()
    print("SysAdmin Security Module Online.")
