"""M3 integration: tool-use Scenario -> ToolUsingAgent -> BasicRunner -> Run -> Evaluators -> Report."""

import json
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from agentlab.agents import ToolUsingAgent
from agentlab.core.models import EventType, Result, RunStatus, Scenario
from agentlab.evaluators import ToolArgsEvaluator, ToolChoiceEvaluator
from agentlab.reporting import render_text_report
from agentlab.runner import BasicRunner


ROOT = Path(__file__).resolve().parents[1]


def load_scenario(rel: str) -> Scenario:
    data = json.loads((ROOT / rel).read_text(encoding="utf-8"))
    return Scenario.from_dict(data)


class TestM3Integration(unittest.TestCase):
    def test_success_scenario_allowed_tool_correct_args(self):
        scenario = load_scenario("scenarios/tool_use/calculator_success.json")
        run = BasicRunner().run(
            scenario=scenario, agent=ToolUsingAgent(), run_id="run-m3-success"
        )
        self.assertEqual(run.status, RunStatus.COMPLETED)
        # Evidence: TOOL_CALL then TOOL_RESULT ok, no execution outside mock framework.
        calls = [e for e in run.events if e.type == EventType.TOOL_CALL]
        results = [e for e in run.events if e.type == EventType.TOOL_RESULT]
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].content["tool"], "calculator_add")
        self.assertEqual(results[0].content["status"], "ok")
        self.assertEqual(results[0].content["result"], {"sum": 5})

        choice = ToolChoiceEvaluator().evaluate(run, scenario)
        args = ToolArgsEvaluator().evaluate(run, scenario)
        self.assertTrue(choice.passed, choice.reason)
        self.assertTrue(args.passed, args.reason)
        result = Result(
            id="result-m3-success",
            run_id=run.id,
            scenario_id=scenario.id,
            created_at=run.ended_at or run.started_at,
            scores=[choice, args],
            metrics={"events": len(run.events)},
        )
        self.assertTrue(result.overall_passed)
        report = render_text_report(run, result=result)
        self.assertIn("PASS", report)

    def test_failure_scenario_disallowed_tool_denied_not_executed(self):
        scenario = load_scenario("scenarios/tool_use/disallowed_tool_failure.json")
        self.assertEqual(scenario.allowed_tools, ["calculator_add"])
        run = BasicRunner().run(
            scenario=scenario, agent=ToolUsingAgent(), run_id="run-m3-failure"
        )
        # Run lifecycle completes (policy denial handled as recorded outcome); tool not executed.
        self.assertEqual(run.status, RunStatus.COMPLETED)
        calls = [e for e in run.events if e.type == EventType.TOOL_CALL]
        results = [e for e in run.events if e.type == EventType.TOOL_RESULT]
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].content["tool"], "echo_text")
        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0].content,
            {
                "tool": "echo_text",
                "call_id": calls[0].content["call_id"],
                "status": "denied",
                "reason": "tool_not_allowed",
                "allowed_tools": ["calculator_add"],
            },
        )

        choice = ToolChoiceEvaluator().evaluate(run, scenario)
        args = ToolArgsEvaluator().evaluate(run, scenario)
        self.assertFalse(choice.passed, choice.reason)
        # args fail because expected args are for calculator_add but attempted call is echo_text with different args
        self.assertFalse(args.passed, args.reason)
        self.assertTrue(choice.evidence_event_ids)

        result = Result(
            id="result-m3-failure",
            run_id=run.id,
            scenario_id=scenario.id,
            created_at=run.ended_at or run.started_at,
            scores=[choice, args],
            metrics={"events": len(run.events)},
        )
        self.assertFalse(result.overall_passed)


    def test_report_contains_actual_evidence_event_ids(self):
        scenario = load_scenario("scenarios/tool_use/calculator_success.json")
        run = BasicRunner().run(
            scenario=scenario, agent=ToolUsingAgent(), run_id="run-report-evidence"
        )
        score = ToolChoiceEvaluator().evaluate(run, scenario)
        self.assertTrue(score.evidence_event_ids)
        result = Result(
            id="result-report-evidence",
            run_id=run.id,
            scenario_id=scenario.id,
            created_at=run.ended_at or run.started_at,
            scores=[score],
            metrics={},
        )

        report = render_text_report(run, result=result)

        for event_id in score.evidence_event_ids:
            with self.subTest(event_id=event_id):
                self.assertIn(event_id, report)

if __name__ == "__main__":
    unittest.main()
