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
        self.api_key = os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY missing.")

        self.sysadmin = Assistant(
            llm={'model': 'qwen-max'},
            name='Qwen Security Engineer',
            description='Automated Security Patcher.',
            function_list=['github_omniscience']
        )

    def patch_security_vulnerability(self, risk_report):
        """Fixes security risks identified by Alibaba SAS."""
        logger.info(f"🚨 PATCHING RISK: {risk_report[:50]}...")

        prompt = f"""
        SECURITY VULNERABILITY DETECTED.
        DETAILS: {risk_report}
        INSTRUCTION: Find the file, fix the issue using env vars, and commit the patch.
        """
        response = self.sysadmin.run(messages=[{'role': 'user', 'content': prompt}])
        result = ""
        for chunk in response:
            result += chunk.get('content', '')
        return result
