import logging
from typing import Dict


class MultiObjReward:
    """
    Calculates a reward score based on a multi-objective function.
    """

    def __init__(self, base_service):
        self.base = base_service
        self.log = logging.getLogger("MultiObjReward")
        # Weights for the reward function.
        self.weights = {"success": 1.0, "risk": -2.0}  # Penalize risk

    def score(self, metrics: Dict) -> float:
        """
        Scores the execution metrics based on the weighted objectives.
        """
        if not isinstance(metrics, dict):
            raise ValueError("Metrics must be a dictionary")

        reward = 0.0
        if "success" in metrics and metrics["success"]:
            reward += self.weights["success"]

        if "risk" in metrics:
            risk_value = metrics.get("risk", 0)
            if isinstance(risk_value, (int, float)):
                reward += risk_value * self.weights["risk"]
            else:
                raise ValueError("Risk value must be a numeric type")

        self.log.info(f"Calculated reward: {reward}")
        return reward