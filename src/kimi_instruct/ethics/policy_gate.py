import logging
from typing import Dict, List, Tuple


class PolicyGate:
    """
    Checks execution metrics against a set of ethical and safety policies.
    """

    def __init__(self, base_service):
        self.base = base_service
        self.log = logging.getLogger("PolicyGate")
        # In a real system, policies would be loaded from a config file or database.
        self.policies = {"max_risk_score": 0.5}

    def check(self, metrics: Dict) -> Tuple[bool, List[str]]:
        """
        Evaluates the metrics against the loaded policies.
        """
        violations = []
        if metrics.get("risk", 0) > self.policies["max_risk_score"]:
            violations.append(f"Risk score {metrics['risk']} exceeds maximum of {self.policies['max_risk_score']}")

        if not violations:
            self.log.info("Policy check passed.")
            return True, []
        else:
            self.log.warning(f"Policy violations detected: {violations}")
            return False, violations
