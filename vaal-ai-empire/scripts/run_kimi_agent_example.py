import sys
import os

# This is a workaround to add the vaal-ai-empire directory to the Python path
# to allow for absolute imports. This is necessary because the script is
# located in a subdirectory.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.kimi_industry_agent import KimiIndustryAgent

def main():
    """
    Main function to run the Kimi Industry Agent.
    """
    agent = KimiIndustryAgent()
    query = "Provide a report on the latest trends in the electric vehicle industry."
    response = agent.run(query)
    print(response)

if __name__ == "__main__":
    main()
