# rainmaker_orchestrator/__init__.py

class RainmakerOrchestrator:
    def __init__(self):
        print("Initializing mock RainmakerOrchestrator")
        self.config = {}

    async def _call_ollama(self, task, context):
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
