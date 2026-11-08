"""Tests for M3 tool evaluators and audit regressions."""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from agentlab.agents import ToolUsingAgent
from agentlab.core.models import Event, EventType, Run, RunStatus, Scenario
from agentlab.evaluators import ToolArgsEvaluator, ToolChoiceEvaluator
from agentlab.runner import BasicRunner


def make_run(scenario: Scenario, run_id: str = "run-tool"):
    return BasicRunner().run(scenario=scenario, agent=ToolUsingAgent(), run_id=run_id)


class TestToolChoiceEvaluator(unittest.TestCase):
    def test_passes_on_allowed_correct_tool(self):
        scen = Scenario(
            id="scen-ok",
            name="ok",
            description="d",
            task="t",
            allowed_tools=["calculator_add"],
            metadata={
                "tool_call": {"name": "calculator_add", "args": {"a": 1, "b": 2}},
                "expected_tool": "calculator_add",
            },
        )
        run = make_run(scen)
        score = ToolChoiceEvaluator().evaluate(run, scen)
        self.assertTrue(score.passed)
        self.assertEqual(score.value, 1.0)
        self.assertTrue(score.evidence_event_ids)

    def test_fails_on_disallowed_tool_attempt(self):
        scen = Scenario(
            id="scen-deny",
            name="deny",
            description="d",
            task="t",
            allowed_tools=["calculator_add"],
            metadata={
                "tool_call": {"name": "echo_text", "args": {"text": "x"}},
                "expected_tool": "calculator_add",
            },
        )
        run = make_run(scen)
        self.assertEqual(run.status, RunStatus.COMPLETED)  # runner completes; tool was denied by policy
        score = ToolChoiceEvaluator().evaluate(run, scen)
        self.assertFalse(score.passed)
        self.assertIn("echo_text", score.reason)
        self.assertIn("calculator_add", score.reason)
        self.assertTrue(
            "denied" in score.reason.lower() or score.metadata.get("denied"),
            msg=f"reason={score.reason!r} metadata={score.metadata!r}",
        )
        self.assertTrue(score.evidence_event_ids)

    def test_requires_completed_run(self):
        scen = Scenario(
            id="scen-nc",
            name="nc",
            description="d",
            task="t",
            allowed_tools=["calculator_add"],
            metadata={
                "tool_call": {"name": "calculator_add", "args": {"a": 1, "b": 2}},
                "expected_tool": "calculator_add",
            },
        )
        run = make_run(scen, run_id="run-nc")
        run.status = RunStatus.FAILED
        score = ToolChoiceEvaluator().evaluate(run, scen)
        self.assertFalse(score.passed)
        self.assertIn("COMPLETED", score.reason)

    def test_fails_when_expected_tool_missing(self):
        scen = Scenario(
            id="scen-noexp",
            name="n",
            description="d",
            task="t",
            allowed_tools=["calculator_add"],
            metadata={"tool_call": {"name": "calculator_add", "args": {"a": 1, "b": 2}}},
        )
        run = make_run(scen)
        score = ToolChoiceEvaluator().evaluate(run, scen)
        self.assertFalse(score.passed)
        self.assertIn("expected_tool", score.reason)


    def test_rejects_result_with_nonmatching_call_id(self):
        run = Run(
            id="run-call-id-mismatch",
            scenario_id="scen-call-id-mismatch",
            agent_id="agent",
            started_at="2026-01-01T00:00:00Z",
            ended_at="2026-01-01T00:00:01Z",
            status=RunStatus.COMPLETED,
            scenario_snapshot={
                "id": "scen-call-id-mismatch",
                "metadata": {"expected_tool": "calculator_add"},
            },
            events=[
                Event(
                    id="call-event",
                    timestamp="2026-01-01T00:00:00Z",
                    type=EventType.TOOL_CALL,
                    content={
                        "tool": "calculator_add",
                        "args": {"a": 1, "b": 2},
                        "call_id": "call-original",
                    },
                ),
                Event(
                    id="result-event",
                    timestamp="2026-01-01T00:00:01Z",
                    type=EventType.TOOL_RESULT,
                    content={
                        "tool": "calculator_add",
                        "call_id": "call-different",
                        "status": "ok",
                    },
                ),
            ],
        )

        score = ToolChoiceEvaluator().evaluate(run)

        self.assertFalse(score.passed)
        self.assertIn("missing_result", score.reason)
        self.assertEqual(score.evidence_event_ids, ["call-event"])

class TestToolArgsEvaluator(unittest.TestCase):
    def test_passes_on_matching_args(self):
        scen = Scenario(
            id="scen-args",
            name="ok",
            description="d",
            task="t",
            allowed_tools=["calculator_add"],
            metadata={
                "tool_call": {"name": "calculator_add", "args": {"a": 2, "b": 3}},
                "expected_tool": "calculator_add",
                "expected_args": {"a": 2, "b": 3},
            },
        )
        run = make_run(scen)
        score = ToolArgsEvaluator().evaluate(run, scen)
        self.assertTrue(score.passed)
        self.assertEqual(score.value, 1.0)
        self.assertTrue(score.evidence_event_ids)

    def test_fails_on_mismatched_args(self):
        scen = Scenario(
            id="scen-badargs",
            name="bad",
            description="d",
            task="t",
            allowed_tools=["calculator_add"],
            metadata={
                "tool_call": {"name": "calculator_add", "args": {"a": 2, "b": 3}},
                "expected_tool": "calculator_add",
                "expected_args": {"a": 9, "b": 9},
            },
        )
        run = make_run(scen)
        score = ToolArgsEvaluator().evaluate(run, scen)
        self.assertFalse(score.passed)
        self.assertIn("mismatch", score.reason.lower())

    def test_requires_completed_run(self):
        scen = Scenario(
            id="scen-nc2",
            name="nc",
            description="d",
            task="t",
            allowed_tools=["calculator_add"],
            metadata={
                "tool_call": {"name": "calculator_add", "args": {"a": 1, "b": 2}},
                "expected_args": {"a": 1, "b": 2},
            },
        )
        run = make_run(scen, run_id="run-nc2")
        run.status = RunStatus.FAILED
        score = ToolArgsEvaluator().evaluate(run, scen)
        self.assertFalse(score.passed)
        self.assertIn("COMPLETED", score.reason)

    def test_fails_when_expected_args_missing(self):
        scen = Scenario(
            id="scen-noargs",
            name="n",
            description="d",
            task="t",
            allowed_tools=["calculator_add"],
            metadata={"tool_call": {"name": "calculator_add", "args": {"a": 1, "b": 2}}},
        )
        run = make_run(scen)
        score = ToolArgsEvaluator().evaluate(run, scen)
        self.assertFalse(score.passed)
        self.assertIn("expected_args", score.reason)

    def test_fails_when_expected_tool_missing_even_if_other_tool_has_matching_args(self):
        # P1 regression: wrong tool has exactly the expected args; must not pass.
        expected_args = {"a": 7, "b": 8}
        run = Run(
            id="run-p1",
            scenario_id="scen-p1",
            agent_id="agent",
            started_at="2026-01-01T00:00:00Z",
            ended_at="2026-01-01T00:00:01Z",
            status=RunStatus.COMPLETED,
            scenario_snapshot={
                "id": "scen-p1",
                "metadata": {"expected_tool": "calculator_add", "expected_args": expected_args},
            },
            events=[
                Event(
                    id="ev1",
                    timestamp="2026-01-01T00:00:00Z",
                    type=EventType.TOOL_CALL,
                    content={"tool": "echo_text", "args": dict(expected_args), "call_id": "c1"},
                ),
                Event(
                    id="ev2",
                    timestamp="2026-01-01T00:00:01Z",
                    type=EventType.TOOL_RESULT,
                    content={"tool": "echo_text", "call_id": "c1", "status": "ok", "result": {"sum": 15}},
                ),
            ],
        )
        score = ToolArgsEvaluator().evaluate(run)
        self.assertFalse(score.passed)
        self.assertIn("calculator_add", score.reason)
        self.assertIn("not found", score.reason.lower())
        self.assertNotEqual(score.metadata.get("tool"), "echo_text")

if __name__ == "__main__":
    unittest.main()
