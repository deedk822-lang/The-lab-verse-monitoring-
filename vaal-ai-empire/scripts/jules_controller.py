# vaal-ai-empire/scripts/jules_controller.py
import os
import sys
import requests
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("JulesController")

class JulesController:
    """
    A client for interacting with the Jules API to create new sessions for autonomous fixes.
    """
    def __init__(self):
        self.api_key = os.getenv("JULES_API_KEY")
        self.api_url = os.getenv("JULES_API_URL", "https://jules.google.com/session")
        self.repo = os.getenv("GITHUB_REPOSITORY")

        if not self.api_key:
            raise ValueError("JULES_API_KEY environment variable not set.")
        if not self.repo:
            raise ValueError("GITHUB_REPOSITORY environment variable not set.")

    def new_session(self, prompt: str) -> dict:
        """
        Creates a new remote session to delegate a task to Jules.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "repo": self.repo,
            "session": prompt
        }

        logger.info(f"Creating new Jules session for repo '{self.repo}' with prompt: '{prompt}'")

        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

            session_data = response.json()
            logger.info(f"Successfully created session: {session_data.get('id')}")
            return session_data

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create Jules session: {e}")
            raise

def main():
    """
    Main function to run the Jules controller from the command line.
    """
    if len(sys.argv) < 2:
        logger.error("Usage: python jules_controller.py \"<prompt>\"")
        sys.exit(1)

    prompt = sys.argv[1]

    try:
        controller = JulesController()
        controller.new_session(prompt)
    except (ValueError, requests.exceptions.RequestException) as e:
        logger.fatal(f"A critical error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
