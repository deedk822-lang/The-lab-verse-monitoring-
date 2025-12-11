# vaal-ai-empire/scripts/jules_controller.py
import os
import sys
import requests
import logging
import json
import subprocess

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("JulesController")

class JulesController:
    """
    A context-aware client for interacting with the Jules API to create new sessions for autonomous fixes.
    """
    def __init__(self):
        self.api_key = os.getenv("JULES_API_KEY")
        self.api_url = os.getenv("JULES_API_URL", "https://jules.google.com/session")
        self.repo = os.getenv("GITHUB_REPOSITORY")

        if not self.api_key:
            raise ValueError("JULES_API_KEY environment variable not set.")
        if not self.repo:
            raise ValueError("GITHUB_REPOSITORY environment variable not set.")

    def _find_and_checkout_fix_branch(self) -> str:
        """
        Searches for a relevant fix branch and checks it out.
        Returns the name of the checked-out branch.
        """
        logger.info("Searching for a relevant fix branch...")
        try:
            # Fetch all remote branches
            subprocess.run(["git", "fetch", "origin"], check=True)

            # Get list of remote branches
            result = subprocess.run(["git", "branch", "-r"], capture_output=True, text=True, check=True)
            branches = result.stdout.strip().split("\n")

            # Find a suitable branch (prefer 'fix' or 'hotfix' branches)
            fix_branch = None
            for branch in branches:
                branch_name = branch.strip()
                if "origin/fix/" in branch_name or "origin/hotfix/" in branch_name:
                    fix_branch = branch_name.replace("origin/", "")
                    break

            if fix_branch:
                logger.info(f"Found a potential fix branch: {fix_branch}. Checking it out...")
                subprocess.run(["git", "checkout", fix_branch], check=True)
                return fix_branch
            else:
                logger.warning("No specific fix branch found. Staying on the current branch.")
                return os.getenv("GITHUB_REF_NAME", "main")

        except subprocess.CalledProcessError as e:
            logger.error(f"Git operation failed: {e}")
            return os.getenv("GITHUB_REF_NAME", "main") # Fallback to current branch

    def _build_tech_stack_profile(self) -> str:
        """
        Scans the repository for key technology indicators and builds a profile.
        """
        profile = ["This repository uses the following technologies:"]

        # Python
        if os.path.exists("requirements.txt"):
            profile.append("- Python: Use `pip install -r requirements.txt` to install dependencies.")
        if os.path.exists("vaal-ai-empire/requirements.txt"):
            profile.append("- Python (Vaal AI Empire): Use `pip install -r vaal-ai-empire/requirements.txt`.")

        # Node.js
        if os.path.exists("package.json"):
            profile.append("- Node.js: Use `npm install` or `npm ci` for dependencies.")

        # Vercel
        if os.path.exists("vercel.json"):
            profile.append("- Vercel: This is a Vercel project. Check `vercel.json` for deployment configuration.")

        # Hugging Face
        if "huggingface" in self._read_file_content("requirements.txt") or \
           "huggingface" in self._read_file_content("vaal-ai-empire/requirements.txt"):
            profile.append("- Hugging Face: The project uses the Hugging Face Hub. Ensure you are logged in with `huggingface-cli login` if needed.")

        # Cohere
        if "cohere" in self._read_file_content("requirements.txt"):
            profile.append("- Cohere: The project uses the Cohere API. The `COHERE_API_KEY` is required.")

        return "\n".join(profile)

    def _read_file_content(self, file_path: str) -> str:
        """Safely reads the content of a file."""
        try:
            with open(file_path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            return ""

    def new_session(self, prompt: str) -> dict:
        """
        Creates a new remote session with a context-rich prompt.
        """
        fix_branch = self._find_and_checkout_fix_branch()
        tech_profile = self._build_tech_stack_profile()
        full_prompt = f"{prompt}\n\nI have checked out the '{fix_branch}' branch to analyze the fix.\n\n--- Tech Stack Context ---\n{tech_profile}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "repo": self.repo,
            "session": full_prompt
        }

        logger.info(f"Creating new Jules session for repo '{self.repo}'")
        logger.info(f"Full Prompt:\n{full_prompt}")

        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()

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
