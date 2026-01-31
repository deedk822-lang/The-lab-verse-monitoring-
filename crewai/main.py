
import json
import os
import sys

from crewai_tools import SerperDevTool
from dotenv import load_dotenv

from crewai import Agent, Crew, Task

load_dotenv()

# Check for topic argument
if len(sys.argv) < 2:
    print("Usage: python main.py <topic>")
    sys.exit(1)

topic = sys.argv[1]

# Get API keys from environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")
serper_api_key = os.getenv("SERPER_API_KEY")

if not openai_api_key or not serper_api_key:
    print("Error: OPENAI_API_KEY or SERPER_API_KEY not found in .env file.")
    sys.exit(1)

search_tool = SerperDevTool()

# Define the researcher agent
researcher = Agent(
  role='Researcher',
  goal=f'Find and summarize the latest news on {topic}',
  backstory="""You're a researcher at a large company.
  You're responsible for analyzing data and providing insights
  to the business.""",
  verbose=False,
  tools=[search_tool]
)

# Define the research task
task = Task(
  description=f'Find and summarize the latest news on {topic}',
  expected_output=f'A bullet list summary of the top 5 most important news on {topic}',
  agent=researcher
)

# Create the crew
crew = Crew(
    agents=[researcher],
    tasks=[task],
    verbose=False
)

# Execute the crew and print the result in JSON format
try:
    result = crew.kickoff()
    output = {
        "result": result,
        "token_usage": crew.usage_metrics
    }
    print(json.dumps(output))
except Exception as e:
    error = {
        "error": str(e)
    }
    print(json.dumps(error))
    sys.exit(1)
