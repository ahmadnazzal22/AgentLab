"""Tests for M2 TaskCompletionEvaluator."""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from agentlab.agents.sample_agent import SampleAgent
from agentlab.core.models import RunStatus, Scenario
from agentlab.evaluators import TaskCompletionEvaluator
from agentlab.runner import BasicRunner


class TestTaskCompletionEvaluator(unittest.TestCase):
    def setUp(self) -> None:
        self.scenario = Scenario(
            id="scen-eval",
            name="Eval",
            description="d",
            task="Say hello",
            metadata={"expected_output": "Hello, world!"},
        )
        self.runner = BasicRunner()
        self.evaluator = TaskCompletionEvaluator()

    def test_passes_completed_run_with_evidence_from_snapshot(self) -> None:
        run = self.runner.run(scenario=self.scenario, agent=SampleAgent(), run_id="run-pass")
        # Evaluate using saved run only (snapshot contains expected_output)
        score = self.evaluator.evaluate(run)
        self.assertTrue(score.passed)
        self.assertEqual(score.value, 1.0)
        self.assertTrue(score.evidence_event_ids)

    def test_fails_when_not_completed(self) -> None:
        run = self.runner.run(scenario=self.scenario, agent=SampleAgent(), run_id="run-nc")
        run.status = RunStatus.FAILED
        score = self.evaluator.evaluate(run, self.scenario)
        self.assertFalse(score.passed)
        self.assertIn("COMPLETED", score.reason)

    def test_fails_when_no_expected_output(self) -> None:
        scen = Scenario(id="scen-noexp", name="n", description="d", task="t", metadata={})
        run = self.runner.run(scenario=scen, agent=SampleAgent(), run_id="run-noexp")
        score = self.evaluator.evaluate(run, scen)
        self.assertFalse(score.passed)
        self.assertIn("expected_output", score.reason)

    def test_no_hardcoding_uses_scenario_metadata(self) -> None:
        scen = Scenario(
            id="scen-custom",
            name="n",
            description="d",
            task="t",
            metadata={"expected_output": "CUSTOM_TOKEN_123"},
        )
        run = self.runner.run(scenario=scen, agent=SampleAgent(), run_id="run-custom")
        score = self.evaluator.evaluate(run, scen)
        self.assertTrue(score.passed)
        self.assertIn("CUSTOM_TOKEN_123", score.metadata["expected_output"])


if __name__ == "__main__":
    unittest.main()
