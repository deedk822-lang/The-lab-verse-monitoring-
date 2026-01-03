import os
import sys
import logging
# Use Zhipu AI SDK
from zhipuai import ZhipuAI
import zhipuai # For specific error types

# Configure logging for the script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_description(diff_content: str, prompt_template_path: str) -> str:
    """
    Calls the Zhipu AI GLM API using their SDK.
    """
    try:
        with open(prompt_template_path, 'r', encoding='utf-8') as f:
            prompt_template = f.read()

        prompt = prompt_template.replace("{{ DIFF_CONTENT }}", diff_content)

        # Retrieve the API key from the environment variable set by the GitHub Action
        api_key = os.getenv("ZHIPU_API_KEY")
        if not api_key:
            raise ValueError("ZHIPU_API_KEY environment variable is not set.")

        client = ZhipuAI(api_key=api_key)

        # Truncate diff to prevent token limit issues (optional, but good practice)
        MAX_DIFF_LENGTH = 50000
        if len(diff_content) > MAX_DIFF_LENGTH:
            logger.info(f"Diff content truncated from {len(diff_content)} to {MAX_DIFF_LENGTH} characters.")
            diff_content = diff_content[:MAX_DIFF_LENGTH] + "\n\n...[diff truncated for length]"
            prompt = prompt_template.replace("{{ DIFF_CONTENT }}", diff_content) # Re-substitute truncated diff

        response = client.chat.completions.create(
            model="glm-4", # Use the specific model (or glm-4.7 if available and configured)
            messages=[
                {"role": "system", "content": "You are an assistant helping to generate GitHub Pull Request descriptions based on code changes."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000,
        )

        ai_output = response.choices[0].message.content.strip()
        return ai_output

    except FileNotFoundError:
        logger.error(f"Prompt template file '{prompt_template_path}' not found.")
        sys.exit(1)
    except ValueError as e: # Catch the specific error if key is missing
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except zhipuai.APIStatusError as err: # Specific ZhipuAI error
        logger.error(f"ZhipuAI API Error (Status {err.status_code}): {err.message}")
        return f"❌ AI generation failed (API Error {err.status_code}): {err.message}"
    except zhipuai.APITimeoutError: # Specific ZhipuAI error
        logger.error("ZhipuAI API request timed out.")
        return "❌ AI generation timed out. Please try again."
    except Exception as e: # General error
        logger.error(f"Error calling Zhipu AI API: {e}")
        return f"❌ AI generation failed: {str(e)}"

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python generate_pr_description_zhipu.py <diff_file_path> <prompt_template_path>")
        sys.exit(1)

    diff_file_path = sys.argv[1]
    prompt_template_path = sys.argv[2]

    try:
        with open(diff_file_path, 'r', encoding='utf-8') as f:
            diff_content = f.read()
    except FileNotFoundError:
        logger.error(f"Diff file '{diff_file_path}' not found.")
        sys.exit(1)

    ai_description = generate_description(diff_content, prompt_template_path)
    print(ai_description)
