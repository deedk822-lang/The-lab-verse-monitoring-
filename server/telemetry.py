"""
Minimal telemetry helpers - only a lightweight counter is required
for the unit tests.
"""

from dataclasses import dataclass

@dataclass
class Counter:
    """
    A tiny counter that keeps an in-memory count.
    """
    name: str
    _value: int = 0

    def add(self, increment: int, labels: dict[str, str] | None = None) -> None:
        """
        Increment the counter value.
        """
        self._value += increment

# Global counter used by the agent wrapper
msg_sent_counter = Counter(name="msg_sent_total")
