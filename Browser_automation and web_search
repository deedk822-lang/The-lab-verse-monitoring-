import json
from groq import Groq

client = Groq(
    default_headers={
        "Groq-Model-Version": "latest"
    }
)

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "What are the latest models on Groq and what are they good at?",
        }
    ],
    model="groq/compound-mini",
    compound_custom={
        "tools": {
            "enabled_tools": ["browser_automation", "web_search"]
        }
    }
)

message = chat_completion.choices[0].message

# Print the final content
print(message.content)

# Print the reasoning process
print(message.reasoning)

# Print executed tools
if message.executed_tools:
    print(message.executed_tools[0])
