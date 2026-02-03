"""Telemetry helpers for agent responses."""

from dataclasses import dataclass
from typing import Dict


@dataclass
class Counter:
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
