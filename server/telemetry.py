"""
Minimal telemetry helpers - only a lightweight counter is required
for the unit tests. The real deployment can switch this
to an actual Prometheus/OTLP exporter if desired.
"""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class Counter:
    """
    A tiny counter that keeps an in-memory count.
    The real production code should replace this with
    a Prometheus Counter or any other exporter.
    """

    name: str
    _value: int = 0

    def add(self, amount: int, attributes: Optional[Dict[str, str]] = None) -> None:
        """
        Increment the counter value.

        Args:
            amount: how many units to add
            attributes: optional key/value pairs - ignored in this stub
        """
        self._value += amount


# Global counter used by the agent wrapper to emulate the "msg_sent_total"
msg_sent_counter = Counter(name="agent_response")
