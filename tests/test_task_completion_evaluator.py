"""Tests for M2 TaskCompletionEvaluator."""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from agentlab.agents.sample_agent import SampleAgent
from agentlab.core.models import Event, EventType, Run, RunStatus, Scenario
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

    def test_fails_when_expected_output_appears_only_in_task_restatement(self) -> None:
        expected = "Hello, world!"
        run = Run(
            id="run-restate",
            scenario_id="scen-restate",
            agent_id="agent",
            started_at="2026-01-01T00:00:00Z",
            ended_at="2026-01-01T00:00:01Z",
            status=RunStatus.COMPLETED,
            scenario_snapshot={
                "id": "scen-restate",
                "task": f"Please output: {expected}",
                "metadata": {"expected_output": expected},
            },
            events=[
                Event(
                    id="e1",
                    timestamp="2026-01-01T00:00:00Z",
                    type=EventType.AGENT_MESSAGE,
                    content={"role": "assistant", "message": f"Starting task: Please output: {expected}"},
                    metadata={"step": 1},
                ),
                Event(
                    id="e2",
                    timestamp="2026-01-01T00:00:01Z",
                    type=EventType.AGENT_MESSAGE,
                    content={"role": "assistant", "message": "I will try."},
                    metadata={"step": 2},
                ),
            ],
        )
        score = self.evaluator.evaluate(run)
        self.assertFalse(score.passed)
        self.assertTrue(score.evidence_event_ids)  # shows where text was seen
        self.assertIn("completion", score.reason.lower() + " " + "restatement")

    def test_fails_when_ordinary_message_repeats_expected_output(self) -> None:
        expected = "Hello, world!"
        run = Run(
            id="run-ordinary-repeat",
            scenario_id="scen-ordinary-repeat",
            agent_id="agent",
            started_at="2026-01-01T00:00:00Z",
            ended_at="2026-01-01T00:00:01Z",
            status=RunStatus.COMPLETED,
            scenario_snapshot={
                "id": "scen-ordinary-repeat",
                "metadata": {"expected_output": expected},
            },
            events=[
                Event(
                    id="ordinary-message",
                    timestamp="2026-01-01T00:00:01Z",
                    type=EventType.AGENT_MESSAGE,
                    content={"role": "assistant", "message": f"The requested output is {expected}."},
                    metadata={"step": 1},
                ),
            ],
        )

        score = self.evaluator.evaluate(run)

        self.assertFalse(score.passed)
        self.assertEqual(score.evidence_event_ids, ["ordinary-message"])
        self.assertIn("completion evidence", score.reason.lower())

    def test_passes_when_expected_output_in_final_agent_message(self) -> None:
        expected = "Hello, world!"
        run = Run(
            id="run-final",
            scenario_id="scen-final",
            agent_id="agent",
            started_at="2026-01-01T00:00:00Z",
            ended_at="2026-01-01T00:00:01Z",
            status=RunStatus.COMPLETED,
            scenario_snapshot={"id": "scen-final", "metadata": {"expected_output": expected}},
            events=[
                Event(
                    id="e1",
                    timestamp="2026-01-01T00:00:00Z",
                    type=EventType.AGENT_MESSAGE,
                    content={"role": "assistant", "message": "Starting task"},
                    metadata={"step": 1},
                ),
                Event(
                    id="e2",
                    timestamp="2026-01-01T00:00:01Z",
                    type=EventType.AGENT_MESSAGE,
                    content={"role": "assistant", "message": expected, "output": expected},
                    metadata={"step": 2, "final": True},
                ),
            ],
        )
        score = self.evaluator.evaluate(run)
        self.assertTrue(score.passed)


if __name__ == "__main__":
    unittest.main()
