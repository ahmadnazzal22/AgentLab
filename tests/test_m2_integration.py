"""M2 integration test: Scenario -> Sample Agent -> Runner -> Run Record -> Evaluator -> Report."""

import json
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from agentlab.agents import SampleAgent
from agentlab.core.models import Result, RunStatus, Scenario
from agentlab.evaluators import TaskCompletionEvaluator
from agentlab.reporting import render_text_report
from agentlab.runner import BasicRunner


class TestM2Integration(unittest.TestCase):
    def test_full_flow_with_hello_world_scenario(self) -> None:
        root = Path(__file__).resolve().parents[1]
        scenario_path = root / "scenarios" / "task_completion" / "hello_world.json"
        self.assertTrue(scenario_path.is_file(), f"Missing scenario: {scenario_path}")

        data = json.loads(scenario_path.read_text(encoding="utf-8"))
        scenario = Scenario.from_dict(data)
        self.assertEqual(scenario.metadata["expected_output"], "Hello, world!")

        agent = SampleAgent(agent_id="sample-agent")
        runner = BasicRunner()
        run = runner.run(scenario=scenario, agent=agent, run_id="run-hello-001")

        self.assertEqual(run.status, RunStatus.COMPLETED)
        self.assertEqual(run.scenario_id, scenario.id)
        self.assertTrue(run.events)
        # Agent must not mutate run directly - verified by contract/design; runner recorded events.

        evaluator = TaskCompletionEvaluator()
        score = evaluator.evaluate(run, scenario)
        self.assertTrue(score.passed)
        self.assertEqual(score.value, 1.0)

        result = Result(
            id="result-hello-001",
            run_id=run.id,
            scenario_id=scenario.id,
            created_at=run.ended_at or run.started_at,
            scores=[score],
            metrics={"events": len(run.events)},
        )
        self.assertTrue(result.overall_passed)

        report = render_text_report(run, result=result)
        self.assertIn("AgentLab Run Report", report)
        self.assertIn("run-hello-001", report)
        self.assertIn("COMPLETED", report.upper())
        self.assertIn("PASS", report)


if __name__ == "__main__":
    unittest.main()
