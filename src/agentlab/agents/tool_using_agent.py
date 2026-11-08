"""Deterministic tool-using agent for M3 (batch contract).

Contract (unchanged from M2): execute(scenario) -> list[Event]
- Returns events only; does NOT mutate a Run.
- Uses deterministic mock tools via MockToolRegistry.
- Tool attempts are driven by Scenario.metadata["tool_call"] = {"name": str, "args": dict}.
  This keeps behavior data-driven and testable without hardcoding scenario values.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from agentlab.core.models import Event, EventType, Scenario
from agentlab.tools import CalculatorAddTool, EchoTextTool, MockToolRegistry

from .base import Agent


def _default_registry() -> MockToolRegistry:
    return MockToolRegistry([CalculatorAddTool(), EchoTextTool()])


class ToolUsingAgent(Agent):
    """A deterministic agent that performs one tool attempt described by scenario metadata."""

    def __init__(
        self,
        agent_id: str = "tool-using-agent",
        registry: MockToolRegistry | None = None,
    ) -> None:
        self.agent_id = agent_id
        self.registry = registry or _default_registry()

    def _ts(self, step: int) -> str:
        base = datetime(2026, 1, 1, 0, 0, step, tzinfo=timezone.utc)
        return base.isoformat().replace("+00:00", "Z")

    def _event(self, scenario: Scenario, step: int, suffix: str, etype: EventType, content: dict[str, Any]) -> Event:
        return Event(
            id=f"{scenario.id}-evt-{suffix}",
            timestamp=self._ts(step),
            type=etype,
            content=content,
            metadata={"agent_id": self.agent_id, "step": step},
        )

    def execute(self, scenario: Scenario) -> list[Event]:
        events: list[Event] = [
            self._event(
                scenario,
                1,
                "001",
                EventType.AGENT_MESSAGE,
                {"role": "assistant", "message": f"Starting tool task: {scenario.task}"},
            )
        ]

        tool_call = scenario.metadata.get("tool_call")
        if not isinstance(tool_call, dict):
            events.append(
                self._event(
                    scenario,
                    2,
                    "002",
                    EventType.ERROR,
                    {
                        "message": "invalid_scenario_metadata",
                        "error": "Scenario.metadata['tool_call'] must be a dict with 'name' and 'args'",
                    },
                )
            )
            return events

        tool_name = tool_call.get("name")
        args = tool_call.get("args", {})
        if not isinstance(tool_name, str) or not tool_name:
            events.append(
                self._event(
                    scenario,
                    2,
                    "002",
                    EventType.ERROR,
                    {
                        "message": "invalid_tool_call",
                        "error": "tool_call.name must be a non-empty string",
                    },
                )
            )
            return events
        if not isinstance(args, dict):
            events.append(
                self._event(
                    scenario,
                    2,
                    "002",
                    EventType.ERROR,
                    {"message": "invalid_tool_call", "error": "tool_call.args must be a dict"},
                )
            )
            return events

        call_id = f"{scenario.id}-call-001"
        tool_events = self.registry.dispatch(
            tool_name=tool_name,
            args=dict(args),
            allowed_tools=list(scenario.allowed_tools),
            call_id=call_id,
            call_event_id=f"{scenario.id}-evt-002",
            result_event_id=f"{scenario.id}-evt-003",
            call_timestamp=self._ts(2),
            result_timestamp=self._ts(3),
            metadata={"agent_id": self.agent_id},
        )
        events.extend(tool_events)

        # Summarize outcome for traceability; do not execute tools here.
        result_event = tool_events[1] if len(tool_events) > 1 else None
        status = None
        if result_event is not None and isinstance(result_event.content, dict):
            status = result_event.content.get("status")
        if status == "ok":
            result_payload = result_event.content.get("result") if result_event else None
            message = f"Tool {tool_name} completed successfully."
            output = {"tool": tool_name, "status": "ok", "result": result_payload}
        elif status == "denied":
            message = f"Tool {tool_name} was denied by policy."
            output = {
                "tool": tool_name,
                "status": "denied",
                "reason": "tool_not_allowed",
                "executed": False,
            }
        else:
            message = f"Tool {tool_name} did not complete successfully."
            output = {"tool": tool_name, "status": status or "unknown", "executed": False}

        events.append(
            Event(
                id=f"{scenario.id}-evt-004",
                timestamp=self._ts(4),
                type=EventType.AGENT_MESSAGE,
                content={"role": "assistant", "message": message, "output": output},
                metadata={"agent_id": self.agent_id, "step": 4, "final": True},
            )
        )
        return events
