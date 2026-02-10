"""
Minimal telemetry helpers - only a lightweight counter is required
for the unit tests. The real deployment can switch this
to an actual Prometheus/OTLP exporter if desired.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class Counter:
    """
    A tiny counter that keeps an in-memory count.
    The real production code should replace this with
    a Prometheus Counter or any other exporter.
    """

    name: str
    _value: int = 0

    def add(self, increment: int, labels: Dict[str, str] | None = None) -> None:
        """
        Increment the counter value.

        Args:
            increment: how many units to add
            labels: optional key/value pairs - ignored in this stub
        """
        self._value += increment


# Global counter used by the agent wrapper
msg_sent_counter = Counter(name="msg_sent_total")
