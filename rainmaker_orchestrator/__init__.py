# rainmaker_orchestrator/__init__.py

class RainmakerOrchestrator:
    def __init__(self):
        """
        Initialize a mock RainmakerOrchestrator instance.
        
        Prints an initialization message and sets the instance attribute `config` to an empty dictionary.
        """
        print("Initializing mock RainmakerOrchestrator")
        self.config = {}

    async def _call_ollama(self, task, context):
        """
        Provide a mock Ollama response containing a JSON-string payload with company analysis.
        
        Parameters:
            task: The task description or prompt to send to Ollama (unused in the mock).
            context: Additional contextual information for the call (unused in the mock).
        
        Returns:
            dict: A dictionary with a "message" key whose "content" value is a JSON-formatted string containing:
                - company_name: Name of the company (string).
                - summary: Brief summary of analysis (string).
                - intent_score: Numeric score indicating intent (int).
                - suggested_action: Recommended action (string).
        """
        print("Mocking _call_ollama")
        return {
            "message": {
                "content": '{"company_name": "Mock Company", "summary": "Mock summary", "intent_score": 9, "suggested_action": "Mock action"}'
            }
        }

class DirectiveParser:
    pass

class ToolType:
    pass