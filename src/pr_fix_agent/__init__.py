"""
PR Fix Agent Core Library
Production-ready components for error analysis, security validation, and automated fixing
"""

# Importing necessary modules for security validation and analysis
from .security import (
    SecurityError,
    SecurityValidator,
    InputValidator,
    RateLimiter
)

# Importing necessary modules for analyzing and fixing production errors
from .analyzer import (
    PRErrorAnalyzer,
    PRErrorFixer
)

# Importing the Ollama Agent and its related exceptions
from .ollama_agent import OllamaAgent, OllamaQueryError

# Importing observability features such as cost tracking and budget exceeded error handling
from .observability import CostTracker, LLMCost, BudgetExceededError, ObservableOllamaAgent

# Importing models and model selectors for managing different types of models
from .models import ModelSpec, ModelSelector

# Importing orchestration functions to manage code reviews
from .orchestrator import CodeReviewOrchestrator
from .security import InputValidator, RateLimiter, SecurityError, SecurityValidator

# Function to check if a value is within a valid range
def validate_value(value, min_val, max_val):
    """
    Validates if the input value falls within the specified range.
    
    :param value: The value to be validated.
    :param min_val: The minimum allowed value.
    :param max_val: The maximum allowed value.
    :return: True if the value is within the range, False otherwise.
    """
    return min_val <= value <= max_val

# Function to log an error
def log_error(error):
    """
    Logs an error message in a structured format.
    
    :param error: The error message to be logged.
    """
    print(f"Error: {error}")

# Example usage of the SecurityValidator class
if __name__ == "__main__":
    # Create a RateLimiter instance
    rate_limiter = RateLimiter(max_requests=10, interval_seconds=60)

    # Validate a sample value
    sample_value = 5
    if validate_value(sample_value, min_val=1, max_val=10):
        print("Value is within the valid range.")
    else:
        log_error("Value is outside the valid range.")

    # Example usage of the OllamaAgent class
    try:
        ollama_agent = OllamaAgent(model="gpt-4")
        response = ollama_agent.generate(prompt="Hello, world!")
        print(response)
    except OllamaQueryError as e:
        log_error(str(e))

    # Example usage of the CodeReviewOrchestrator class
    try:
        code_review_result = CodeReviewOrchestrator.submit_code_review("example.py", "New implementation.")
        if code_review_result == "Approved":
            print("Code review passed.")
        else:
            log_error(f"Code review failed: {code_review_result}")
    except Exception as e:
        log_error(str(e))
