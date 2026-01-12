import logging
import json
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

# Mock client for now
class MockKimiClient:
    async def generate_hotfix(self, prompt: str):
        # In a real scenario, this would call the Kimi API
        """
        Generate a mocked hotfix patch string based on the provided prompt.
        
        Parameters:
            prompt (str): Text describing the issue or context to include in the hotfix header.
        
        Returns:
            str: A mocked hotfix payload containing a comment referencing the prompt and a console.log statement.
        """
        return f"/* Hotfix for: {prompt} */\nconsole.log('This is a mocked hotfix');"

class AlertPayload(BaseModel):
    # Based on Prometheus AlertManager webhook format
    status: str
    labels: dict
    annotations: dict
    startsAt: str
    endsAt: str
    generatorURL: str

class Blueprint(BaseModel):
    file_path: str
    code_patch: str
    description: str

class SelfHealingAgent:
    def __init__(self, kimi_client=None):
        """
        Initialize the SelfHealingAgent with an optional Kimi client.
        
        Parameters:
            kimi_client (optional): Client used to generate hotfix patches. If not provided, a MockKimiClient instance is created and used.
        """
        self.kimi_client = kimi_client or MockKimiClient() # Replace with actual KimiApiClient later

    def _validate_alert(self, alert: dict) -> bool:
        """
        Validate that a dictionary conforms to the expected Prometheus AlertManager payload schema.
        
        Parameters:
            alert (dict): Alert payload to validate (expected fields: status, labels, annotations, startsAt, endsAt, generatorURL).
        
        Returns:
            bool: `True` if the alert matches the expected schema, `False` otherwise.
        """
        try:
            AlertPayload.parse_obj(alert)
            return True
        except ValidationError as e:
            logger.error(f"Invalid alert format: {e}")
            return False

    def _validate_blueprint(self, blueprint: dict) -> bool:
        """
        Validate the structure and safety of a generated blueprint.
        
        Parameters:
            blueprint (dict): Blueprint data to validate.
        
        Returns:
            bool: `True` if the blueprint conforms to the Blueprint model, `False` otherwise.
        
        Notes:
            Logs an error when validation fails and logs a warning if `code_patch` contains potentially destructive keywords such as "DROP" or "DELETE".
        """
        try:
            Blueprint.parse_obj(blueprint)
            # Add more sophisticated checks here, like syntax validation
            if "DROP" in blueprint.get("code_patch", "") or "DELETE" in blueprint.get("code_patch", ""):
                 logger.warning("Potential destructive operation in blueprint.")
                 # In a real system, this might require manual approval
            return True
        except ValidationError as e:
            logger.error(f"Invalid blueprint format: {e}")
            return False

    def _calculate_confidence(self, blueprint: dict) -> float:
        """
        Estimate a confidence score for a generated blueprint.
        
        Parameters:
            blueprint (dict): Blueprint data with expected keys:
                - file_path (str): Target file path (optional for scoring).
                - code_patch (str): Proposed code changes; presence of "TODO" lowers confidence.
                - description (str): Human-readable description; short descriptions lower confidence.
        
        Returns:
            float: Confidence score between 0.0 and 1.0. Starts from 0.7, decreases by 0.2 if `code_patch` contains "TODO" and by 0.1 if `description` length is less than 20 characters; result is clamped to the [0.0, 1.0] range.
        """
        # Simple confidence logic for now
        score = 0.7
        if "TODO" in blueprint.get("code_patch", ""):
            score -= 0.2
        if len(blueprint.get("description", "")) < 20:
            score -= 0.1
        return max(0.0, min(1.0, score))

    def _assess_impact(self, blueprint: dict) -> str:
        """
        Evaluate the expected impact level based on the blueprint's target file path.
        
        Parameters:
            blueprint (dict): A blueprint mapping that should include a "file_path" key used to determine affected area.
        
        Returns:
            str: A human-readable impact description: "Critical: Modifies authentication or authorization logic." if the file path includes "auth", "High: Modifies database schema or queries." if it includes "database", or "Low: General application logic change." otherwise.
        """
        if "database" in blueprint.get("file_path", ""):
            return "High: Modifies database schema or queries."
        if "auth" in blueprint.get("file_path", ""):
            return "Critical: Modifies authentication or authorization logic."
        return "Low: General application logic change."


    async def _generate_blueprint(self, alert: dict) -> dict:
        """
        Create a hotfix blueprint (file_path, code_patch, description) from the alert's annotations.
        
        Builds a prompt from alert.annotations.summary and alert.annotations.description, asks the configured kimi client for a hotfix, and returns the parsed JSON as the blueprint. If the client's response cannot be parsed as JSON, returns a fallback blueprint with file_path set to "unknown.py" and code_patch containing the raw response.
        
        Parameters:
            alert (dict): Prometheus AlertManager-like alert payload; expected to include `annotations` with optional `summary` and `description`.
        
        Returns:
            dict: A blueprint with keys:
                - "file_path" (str): target file to modify,
                - "code_patch" (str): the suggested patch content,
                - "description" (str): human-readable explanation. 
              If parsing fails, returns a fallback dict where "file_path" is "unknown.py" and "code_patch" is the raw generated output.
        """
        summary = alert.get("annotations", {}).get("summary", "No summary")
        description = alert.get("annotations", {}).get("description", "No description")

        prompt = f"""
        Analyze the following alert and generate a hotfix blueprint in JSON format.
        The JSON should have three keys: 'file_path', 'code_patch', and 'description'.

        Alert Summary: {summary}
        Alert Description: {description}

        Based on this, suggest a file to modify and the code patch to apply.
        """

        generated_code = await self.kimi_client.generate_hotfix(prompt)

        try:
            blueprint = json.loads(generated_code)
            return blueprint
        except Exception:
            return {
                "file_path": "unknown.py",
                "code_patch": generated_code,
                "description": "Generated hotfix, but failed to parse as structured JSON."
            }


    async def process_alert(self, alert: dict) -> dict:
        """
        Process a Prometheus AlertManager-style alert to produce a validated hotfix blueprint and associated metrics.
        
        Parameters:
            alert (dict): Alert payload expected to match the AlertPayload schema (e.g., contains keys such as
                `status`, `labels`, `annotations`, `startsAt`, `endsAt`, `generatorURL`).
        
        Returns:
            result (dict): Dictionary with the following keys:
                - "blueprint" (dict): Validated blueprint containing `file_path`, `code_patch`, and `description`.
                - "confidence" (float): Confidence score for the blueprint, clamped between 0.0 and 1.0.
                - "estimated_impact" (str): Human-readable assessment of the potential impact.
        
        Raises:
            ValueError: If the incoming alert fails validation or if the generated blueprint is invalid.
        """
        if not self._validate_alert(alert):
            raise ValueError("Invalid alert format")

        blueprint = await self._generate_blueprint(alert)

        if not self._validate_blueprint(blueprint):
            raise ValueError("Invalid blueprint generated")

        return {
            "blueprint": blueprint,
            "confidence": self._calculate_confidence(blueprint),
            "estimated_impact": self._assess_impact(blueprint)
        }