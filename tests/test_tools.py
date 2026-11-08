"""Tests for M3 mock tool framework."""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from agentlab.core.models import EventType
from agentlab.tools import CalculatorAddTool, EchoTextTool, MockTool, MockToolRegistry, ToolExecutionError


class SpyTool(MockTool):
    name = "spy_tool"

    def __init__(self) -> None:
        self.called = False
        self.last_args = None

    def invoke(self, args):
        self.called = True
        self.last_args = dict(args)
        return {"spied": True}


class TestBuiltinMocks(unittest.TestCase):
    def test_calculator_add_deterministic(self):
        tool = CalculatorAddTool()
        self.assertEqual(tool.invoke({"a": 2, "b": 3}), {"sum": 5})
        self.assertEqual(tool.invoke({"a": -1, "b": 1.5}), {"sum": 0.5})

    def test_calculator_add_rejects_invalid_args(self):
        tool = CalculatorAddTool()
        with self.assertRaises(ToolExecutionError):
            tool.invoke({"a": True, "b": 1})
        with self.assertRaises(ToolExecutionError):
            tool.invoke({"a": 1})

    def test_echo_text(self):
        tool = EchoTextTool()
        self.assertEqual(tool.invoke({"text": "hi"}), {"text": "hi"})


class TestMockToolRegistry(unittest.TestCase):
    def _dispatch(self, registry, **overrides):
        base = dict(
            tool_name="calculator_add",
            args={"a": 2, "b": 3},
            allowed_tools=["calculator_add"],
            call_id="c1",
            call_event_id="e1",
            result_event_id="e2",
            call_timestamp="2026-01-01T00:00:00Z",
            result_timestamp="2026-01-01T00:00:01Z",
            metadata={"m": 1},
        )
        base.update(overrides)
        return registry.dispatch(**base)

    def test_allowed_tool_executes_and_returns_call_then_result(self):
        reg = MockToolRegistry([CalculatorAddTool()])
        events = self._dispatch(reg)
        self.assertEqual(len(events), 2)
        call, result = events
        self.assertEqual(call.type, EventType.TOOL_CALL)
        self.assertEqual(call.content["tool"], "calculator_add")
        self.assertEqual(call.content["args"], {"a": 2, "b": 3})
        self.assertEqual(call.content["call_id"], "c1")
        self.assertEqual(result.type, EventType.TOOL_RESULT)
        self.assertEqual(result.content["status"], "ok")
        self.assertEqual(result.content["result"], {"sum": 5})
        self.assertEqual(result.content["call_id"], "c1")
        self.assertEqual(result.content["tool"], "calculator_add")

    def test_disallowed_tool_denied_without_execution(self):
        spy = SpyTool()
        reg = MockToolRegistry([spy])
        events = self._dispatch(
            reg,
            tool_name="spy_tool",
            args={"x": 1},
            allowed_tools=["calculator_add"],  # spy_tool not allowed
        )
        self.assertFalse(spy.called, "disallowed tool must not be executed")
        self.assertEqual(len(events), 2)
        call, result = events
        self.assertEqual(call.type, EventType.TOOL_CALL)
        self.assertEqual(call.content["tool"], "spy_tool")
        self.assertEqual(call.content["args"], {"x": 1})
        self.assertEqual(call.content["call_id"], "c1")
        self.assertEqual(result.type, EventType.TOOL_RESULT)
        self.assertEqual(
            result.content,
            {
                "tool": "spy_tool",
                "call_id": "c1",
                "status": "denied",
                "reason": "tool_not_allowed",
                "allowed_tools": ["calculator_add"],
            },
        )

    def test_registered_but_not_in_allowlist_denied(self):
        reg = MockToolRegistry([EchoTextTool(), CalculatorAddTool()])
        events = self._dispatch(
            reg,
            tool_name="echo_text",
            args={"text": "hi"},
            allowed_tools=["calculator_add"],
        )
        call, result = events
        self.assertEqual(call.type, EventType.TOOL_CALL)
        self.assertEqual(result.content["status"], "denied")
        self.assertEqual(result.content["reason"], "tool_not_allowed")
        self.assertEqual(result.content["tool"], "echo_text")
        self.assertEqual(result.content["allowed_tools"], ["calculator_add"])

    def test_tool_not_found_when_allowed(self):
        reg = MockToolRegistry([])
        events = self._dispatch(reg, tool_name="missing", allowed_tools=["missing"])
        result = events[1]
        self.assertEqual(result.content["status"], "error")
        self.assertEqual(result.content["reason"], "tool_not_found")

    def test_tool_execution_error_captured(self):
        reg = MockToolRegistry([CalculatorAddTool()])
        events = self._dispatch(
            reg,
            tool_name="calculator_add",
            args={"a": "bad", "b": 1},
            allowed_tools=["calculator_add"],
        )
        result = events[1]
        self.assertEqual(result.content["status"], "error")
        self.assertEqual(result.content["reason"], "tool_execution_error")

    def test_dispatch_returns_defensive_args_copy(self):
        reg = MockToolRegistry([CalculatorAddTool()])
        args = {"a": 2, "b": 3}
        events = self._dispatch(reg, args=args)
        args["a"] = 999
        self.assertEqual(events[0].content["args"]["a"], 2)

    def test_duplicate_tool_registration_rejected(self):
        reg = MockToolRegistry([CalculatorAddTool()])
        with self.assertRaises(ValueError) as ctx:
            reg.register(CalculatorAddTool())
        self.assertIn("duplicate", str(ctx.exception).lower())

    def test_missing_allowlist_none_denies_and_does_not_execute(self):
        spy = SpyTool()
        reg = MockToolRegistry([spy])
        events = self._dispatch(
            reg,
            tool_name="spy_tool",
            args={"x": 1},
            allowed_tools=None,
        )
        self.assertFalse(spy.called, "tool must not execute when allowlist is missing")
        call, result = events
        self.assertEqual(call.type, EventType.TOOL_CALL)
        self.assertEqual(call.content["tool"], "spy_tool")
        self.assertEqual(result.content["status"], "denied")
        self.assertEqual(result.content["reason"], "tool_not_allowed")
        self.assertEqual(result.content["tool"], "spy_tool")
        self.assertEqual(result.content["call_id"], "c1")
        self.assertEqual(result.content["allowed_tools"], [])


if __name__ == "__main__":
    unittest.main()
