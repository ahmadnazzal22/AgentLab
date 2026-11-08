"""Tests for M3 ToolUsingAgent."""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from agentlab.agents import ToolUsingAgent
from agentlab.core.models import EventType, Scenario


class TestToolUsingAgent(unittest.TestCase):
    def _scenario(self, **meta_overrides):
        meta = {
            "tool_call": {"name": "calculator_add", "args": {"a": 2, "b": 3}},
            "expected_tool": "calculator_add",
            "expected_args": {"a": 2, "b": 3},
        }
        meta.update(meta_overrides)
        return Scenario(
            id="scen-tool",
            name="Tool test",
            description="d",
            task="Add numbers",
            allowed_tools=["calculator_add"],
            metadata=meta,
        )

    def test_success_produces_tool_call_and_result(self):
        agent = ToolUsingAgent(agent_id="ta")
        events = agent.execute(self._scenario())
        self.assertIsInstance(events, list)
        types = [str(e.type) for e in events]
        self.assertIn("tool_call", types)
        self.assertIn("tool_result", types)
        self.assertIn("agent_message", types)
        call = next(e for e in events if e.type == EventType.TOOL_CALL)
        result = next(e for e in events if e.type == EventType.TOOL_RESULT)
        self.assertEqual(call.content["tool"], "calculator_add")
        self.assertEqual(call.content["args"], {"a": 2, "b": 3})
        self.assertEqual(result.content["status"], "ok")
        self.assertEqual(result.content["result"], {"sum": 5})
        self.assertEqual(call.content["call_id"], result.content["call_id"])

    def test_disallowed_attempt_records_denied_not_executed(self):
        scen = self._scenario(
            tool_call={"name": "echo_text", "args": {"text": "x"}},
            allowed_tools=["calculator_add"],
        )
        # ensure scenario allowed_tools override is respected
        scen = Scenario(
            id="scen-deny",
            name="Deny",
            description="d",
            task="t",
            allowed_tools=["calculator_add"],
            metadata={"tool_call": {"name": "echo_text", "args": {"text": "x"}}},
        )
        agent = ToolUsingAgent(agent_id="ta")
        events = agent.execute(scen)
        call = next(e for e in events if e.type == EventType.TOOL_CALL)
        result = next(e for e in events if e.type == EventType.TOOL_RESULT)
        self.assertEqual(call.content["tool"], "echo_text")
        self.assertEqual(result.content["status"], "denied")
        self.assertEqual(result.content["reason"], "tool_not_allowed")
        self.assertEqual(result.content["tool"], "echo_text")
        self.assertIn("allowed_tools", result.content)
        self.assertEqual(result.content["allowed_tools"], ["calculator_add"])
        final = [e for e in events if e.type == EventType.AGENT_MESSAGE and e.metadata.get("final")]
        self.assertTrue(final)
        self.assertFalse(final[0].content["output"]["executed"])

    def test_deterministic_event_ids_and_timestamps(self):
        scen = self._scenario()
        a1 = ToolUsingAgent().execute(scen)
        a2 = ToolUsingAgent().execute(scen)
        self.assertEqual([e.id for e in a1], [e.id for e in a2])
        self.assertEqual([e.timestamp for e in a1], [e.timestamp for e in a2])
        self.assertEqual([e.to_dict() for e in a1], [e.to_dict() for e in a2])

    def test_missing_tool_call_metadata_returns_error_event(self):
        scen = Scenario(
            id="scen-bad",
            name="Bad",
            description="d",
            task="t",
            allowed_tools=["calculator_add"],
            metadata={},
        )
        events = ToolUsingAgent().execute(scen)
        self.assertTrue(any(e.type == EventType.ERROR for e in events))
        self.assertFalse(any(e.type == EventType.TOOL_CALL for e in events))

    def test_does_not_require_run_object(self):
        # Contract: execute takes Scenario only and returns events.
        agent = ToolUsingAgent()
        result = agent.execute(self._scenario())
        self.assertEqual(len(result), 4)  # msg, call, result, final msg


if __name__ == "__main__":
    unittest.main()
