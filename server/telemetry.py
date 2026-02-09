 codex/add-initial-configuration-and-server-files
"""
Minimal telemetry helpers - only a lightweight counter is required
for the unit tests. The real deployment can switch this
to an actual Prometheus/OTLP exporter if desired.
"""

"""Telemetry helpers for agent responses."""
 codex/add-mypy-configuration-and-server-components

from dataclasses import dataclass
from typing import Dict


@dataclass
class Counter:
 codex/add-initial-configuration-and-server-files
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


# Global counter used by the agent wrapper to emulate the "msg_sent_total"
msg_sent_counter = Counter(name="msg_sent_total")

    """Minimal counter shim compatible with OpenTelemetry-style counters."""

    name: str

    def add(self, amount: int, attributes: Dict[str, str] | None = None) -> None:
 codex/add-mypy-configuration-and-server-components

        """
        Accepts an increment value and optional attributes for a counter but performs no operation.
        
        Parameters:
            amount (int): The amount to add to the counter (ignored).
            attributes (Dict[str, str] | None): Optional key/value attributes associated with the increment (ignored).
        """
 codex/implement-real-ollama-integration
        _ = amount
        _ = attributes


 codex/add-mypy-configuration-and-server-components
msg_sent_counter = Counter("agent_response")

msg_sent_counter = Counter("agent_response")
 codex/implement-real-ollama-integration
 codex/add-mypy-configuration-and-server-components
