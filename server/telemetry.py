"""Telemetry helpers for agent responses."""

from dataclasses import dataclass
from typing import Dict


@dataclass
class Counter:
    """Minimal counter shim compatible with OpenTelemetry-style counters."""

    name: str

    def add(self, amount: int, attributes: Dict[str, str] | None = None) -> None:
        _ = amount
        _ = attributes


msg_sent_counter = Counter("agent_response")
