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
        reward = 0.0
        if metrics.get("success", False):
            reward += self.weights["success"]

        reward += metrics.get("risk", 0) * self.weights["risk"]

        self.log.info(f"Calculated reward: {reward}")
        return reward
