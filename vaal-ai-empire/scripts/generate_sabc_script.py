import os
import sys
from argparse import ArgumentParser

# Adjust path to import KimiAPI
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from api.kimi import KimiAPI
except (ImportError, ValueError) as e:
    print("Error: Could not import KimiAPI. Make sure your environment is set up correctly.")
    print(f"Details: {e}")
    sys.exit(1)


def generate_playwright_script(kimi_api, username, password, ad_description):
    """
    Uses the KimiAPI to generate a Playwright script for SABC+ automation.
    """
    prompt = f"""
    Write a complete, executable Python script using Playwright that performs the following actions:

    1.  **Launch Browser**: Launch a new Chromium browser instance.
    2.  **Navigate to SABC+**: Open the page "https://www.sabcplus.com/".
    3.  **Login**:
        - Click the login button.
        - Fill in the username field with the value: "{username}"
        - Fill in the password field with the value: "{password}"
        - Click the final login submission button.
    4.  **Navigate to Live Section**: After logging in, click the navigation link or button that leads to the "Live" or "Live TV" section.
    5.  **Ad Detection**:
        - Once on the live TV page, continuously monitor the screen content.
        - Implement a visual check to detect if an advertisement matching the following description is currently playing: "{ad_description}". This could involve looking for specific text, logos, or brand colors.
        - The script should print a clear message to the console: "AD DETECTED: [description]" if the ad is found, or "STATUS: Still monitoring..." if not.
    6.  **Loop and Timeout**: The script should run this detection in a loop for a maximum of 5 minutes before timing out and printing "Error: Ad not detected within 5 minutes."
    7.  **Error Handling**: Include `try...except` blocks to handle potential errors like login failure, elements not being found, or page load issues.
    8.  **Dependencies**: The script should be self-contained. Assume Playwright is installed (`pip install playwright`).

    Provide only the Python code, without any introductory text or explanations.
    """

    print("🤖 Generating Playwright script with Kimi... (This might take a moment)")
    try:
        response = kimi_api.generate_content(prompt, max_tokens=1500)
        return response["text"]
    except Exception as e:
        print(f"❌ An error occurred during script generation: {e}")
        return None


def main():
    parser = ArgumentParser(
        description="Generate a Playwright script for SABC+ ad detection using the Sovereign AI Engine."
    )
    parser.add_argument("--username", required=True, help="SABC+ login username.")
    parser.add_argument("--password", required=True, help="SABC+ login password.")
    parser.add_argument(
        "--ad-description",
        required=True,
        help="A clear description of the ad to detect (e.g., 'The red Atlas TV ad with our logo').",
    )
    parser.add_argument(
        "--output-file", default="sabc_ad_detector.py", help="The name of the output Python script file."
    )

    args = parser.parse_args()

    try:
        kimi_api = KimiAPI()
    except (ImportError, ValueError) as e:
        print(f"Failed to initialize KimiAPI: {e}")
        print("Please ensure your KIMI_VLLM_ENDPOINT is configured in your .env file.")
        sys.exit(1)

    generated_code = generate_playwright_script(kimi_api, args.username, args.password, args.ad_description)

    if generated_code:
        # Clean up the code block if the model wraps it in markdown
        if generated_code.strip().startswith("```python"):
            generated_code = generated_code.strip()[9:]
            if generated_code.strip().endswith("```"):
                generated_code = generated_code.strip()[:-3]

        with open(args.output_file, "w") as f:
            f.write(generated_code)

        print(f"\n✅ Successfully generated Playwright script and saved it to '{args.output_file}'")
        print("To run the script:")
        print("1. Install dependencies: pip install playwright && playwright install")
        print(f"2. Execute: python {args.output_file}")


if __name__ == "__main__":
    main()
