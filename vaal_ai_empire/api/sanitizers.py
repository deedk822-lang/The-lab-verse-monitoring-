import re

def sanitize_prompt(prompt: str) -> str:
    """
    Sanitizes a prompt to remove common prompt injection techniques.
    """
    if not isinstance(prompt, str):
        return ""

    # Remove instructions to ignore previous prompts
    prompt = re.sub(r"(ignore|disregard|forget|override) the previous (instructions|prompt|context)", "", prompt, flags=re.IGNORECASE)

    # Remove instructions to reveal the system prompt
    prompt = re.sub(r"reveal your (system prompt|instructions)", "", prompt, flags=re.IGNORECASE)

    # Remove common jailbreaking phrases
    prompt = re.sub(r"stay in character", "", prompt, flags=re.IGNORECASE)
    prompt = re.sub(r"act as", "", prompt, flags=re.IGNORECASE)

    # Remove template-based injections
    prompt = re.sub(r"\{\{.*\}\}", "", prompt)
    prompt = re.sub(r"<\|.*\|>", "", prompt)

    return prompt.strip()
