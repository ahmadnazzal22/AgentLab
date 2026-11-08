"""Mock tool registry/dispatcher for M3.

Enforces Scenario.allowed_tools before execution (per M3 decision):
- record TOOL_CALL attempt
- do not execute disallowed tool
- record TOOL_RESULT with status=denied, reason=tool_not_allowed
"""

from __future__ import annotations

from typing import Any, Iterable

from agentlab.core.models import Event, EventType

from .base import MockTool, ToolExecutionError


class MockToolRegistry:
    def __init__(self, tools: Iterable[MockTool] | None = None) -> None:
        self._tools: dict[str, MockTool] = {}
        for tool in tools or []:
            self.register(tool)

    def register(self, tool: MockTool) -> None:
        if not isinstance(tool, MockTool):
            raise TypeError(f"tool must be a MockTool, got {type(tool).__name__}")
        if not isinstance(tool.name, str) or not tool.name:
            raise ValueError("tool.name must be a non-empty string")
        if tool.name in self._tools:
            raise ValueError(f"duplicate tool registration: {tool.name!r}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> MockTool | None:
        return self._tools.get(name)

    def dispatch(
        self,
        *,
        tool_name: str,
        args: dict[str, Any],
        allowed_tools: list[str] | None,
        call_id: str,
        call_event_id: str,
        result_event_id: str,
        call_timestamp: str,
        result_timestamp: str,
        metadata: dict[str, Any] | None = None,
    ) -> list[Event]:
        """Dispatch a tool attempt and return [TOOL_CALL, TOOL_RESULT] events.

        `allowed_tools` is the explicit allowlist. Deny-by-default: if `allowed_tools` is
        None (missing allowlist) or the tool is not in the allowlist, the tool is NOT
        executed and a denied TOOL_RESULT is returned.
        """
        meta = dict(metadata or {})
        call_event = Event(
            id=call_event_id,
            timestamp=call_timestamp,
            type=EventType.TOOL_CALL,
            content={"tool": tool_name, "args": dict(args), "call_id": call_id},
            metadata=meta,
        )

        if allowed_tools is None:
            result_event = Event(
                id=result_event_id,
                timestamp=result_timestamp,
                type=EventType.TOOL_RESULT,
                content={
                    "tool": tool_name,
                    "call_id": call_id,
                    "status": "denied",
                    "reason": "tool_not_allowed",
                    "allowed_tools": [],
                    "allowlist_missing": True,
                },
                metadata=meta,
            )
            return [call_event, result_event]

        allowlist = list(allowed_tools)
        if tool_name not in allowlist:
            result_event = Event(
                id=result_event_id,
                timestamp=result_timestamp,
                type=EventType.TOOL_RESULT,
                content={
                    "tool": tool_name,
                    "call_id": call_id,
                    "status": "denied",
                    "reason": "tool_not_allowed",
                    "allowed_tools": list(allowlist),
                },
                metadata=meta,
            )
            return [call_event, result_event]

        tool = self._tools.get(tool_name)
        if tool is None:
            result_event = Event(
                id=result_event_id,
                timestamp=result_timestamp,
                type=EventType.TOOL_RESULT,
                content={
                    "tool": tool_name,
                    "call_id": call_id,
                    "status": "error",
                    "reason": "tool_not_found",
                },
                metadata=meta,
            )
            return [call_event, result_event]

        try:
            result = tool.invoke(dict(args))
            result_event = Event(
                id=result_event_id,
                timestamp=result_timestamp,
                type=EventType.TOOL_RESULT,
                content={
                    "tool": tool_name,
                    "call_id": call_id,
                    "status": "ok",
                    "result": result,
                },
                metadata=meta,
            )
        except Exception as exc:  # noqa: BLE001 - mock tool boundary
            result_event = Event(
                id=result_event_id,
                timestamp=result_timestamp,
                type=EventType.TOOL_RESULT,
                content={
                    "tool": tool_name,
                    "call_id": call_id,
                    "status": "error",
                    "reason": "tool_execution_error",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
                metadata=meta,
            )
        return [call_event, result_event]
