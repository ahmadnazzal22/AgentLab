"""Deterministic sample agent for M2.

Produces fixed, predictable events. It reads Scenario.metadata["expected_output"]
when present to produce verifiable output evidence, but does not hardcode the
evaluator's logic or scenario-specific values outside the scenario data.
"""

from __future__ import annotations

from datetime import datetime, timezone

from agentlab.core.models import Event, EventType, Scenario

from .base import Agent


class SampleAgent(Agent):
    """A deterministic agent that completes the task with predictable events."""

    def __init__(self, agent_id: str = "sample-agent") -> None:
        self.agent_id = agent_id

    def _ts(self, step: int) -> str:
        # Deterministic, timezone-aware timestamps derived from step index.
        base = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        return base.replace(second=step).isoformat().replace("+00:00", "Z")

    def execute(self, scenario: Scenario) -> list[Event]:
        expected = scenario.metadata.get("expected_output")
        output_text = str(expected) if expected is not None else f"Completed: {scenario.task}"
        return [
            Event(
                id=f"{scenario.id}-evt-001",
                timestamp=self._ts(1),
                type=EventType.AGENT_MESSAGE,
                content={"role": "assistant", "message": f"Starting task: {scenario.task}"},
                metadata={"agent_id": self.agent_id, "step": 1},
            ),
            Event(
                id=f"{scenario.id}-evt-002",
                timestamp=self._ts(2),
                type=EventType.TOOL_CALL,
                content={"tool": "complete_task", "input": {"task": scenario.task}},
                metadata={"agent_id": self.agent_id, "step": 2},
            ),
            Event(
                id=f"{scenario.id}-evt-003",
                timestamp=self._ts(3),
                type=EventType.TOOL_RESULT,
                content={"tool": "complete_task", "status": "ok", "output": output_text},
                metadata={"agent_id": self.agent_id, "step": 3},
            ),
            Event(
                id=f"{scenario.id}-evt-004",
                timestamp=self._ts(4),
                type=EventType.AGENT_MESSAGE,
                content={"role": "assistant", "message": output_text, "output": output_text},
                metadata={"agent_id": self.agent_id, "step": 4, "final": True},
            ),
        ]
