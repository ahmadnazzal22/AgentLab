"""Tests for M2 BasicRunner."""

import os
import sys
import time
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from agentlab.agents.base import Agent
from agentlab.agents.sample_agent import SampleAgent
from agentlab.core.models import Event, EventType, RunStatus, Scenario
from agentlab.runner import BasicRunner


class ExplodingAgent(Agent):
    def execute(self, scenario: Scenario) -> list[Event]:
        raise RuntimeError("boom")


class TooManyEventsAgent(Agent):
    def execute(self, scenario: Scenario) -> list[Event]:
        return [
            Event(
                id=f"e{i}",
                timestamp="2026-01-01T00:00:00Z",
                type=EventType.AGENT_MESSAGE,
                content={"i": i},
            )
            for i in range(1, 6)
        ]


class SlowAgent(Agent):
    def execute(self, scenario: Scenario) -> list[Event]:
        time.sleep(0.05)
        return [
            Event(
                id="slow1",
                timestamp="2026-01-01T00:00:00Z",
                type=EventType.AGENT_MESSAGE,
                content={"msg": "done"},
            )
        ]


class TestBasicRunner(unittest.TestCase):
    def setUp(self) -> None:
        self.scenario = Scenario(
            id="scen-run",
            name="Run",
            description="d",
            task="task",
            max_steps=10,
            timeout_seconds=5.0,
            metadata={"expected_output": "Hello, world!"},
        )

    def test_records_agent_events_via_run_lifecycle(self) -> None:
        runner = BasicRunner()
        run = runner.run(scenario=self.scenario, agent=SampleAgent(), run_id="run-001")
        self.assertEqual(run.status, RunStatus.COMPLETED)
        self.assertIsNotNone(run.ended_at)
        # includes agent events plus runner system events
        self.assertGreaterEqual(len(run.events), 4)
        self.assertTrue(any(e.content.get("message") == "run_started" for e in run.events))
        self.assertTrue(any(e.content.get("message") == "run_finished" for e in run.events))

    def test_agent_error_marks_failed(self) -> None:
        runner = BasicRunner()
        run = runner.run(scenario=self.scenario, agent=ExplodingAgent(), run_id="run-err")
        self.assertEqual(run.status, RunStatus.FAILED)
        self.assertTrue(any(e.type == EventType.ERROR for e in run.events))

    def test_post_execution_max_steps_exceeded(self) -> None:
        scen = Scenario(id="scen-max", name="n", description="d", task="t", max_steps=2)
        runner = BasicRunner()
        run = runner.run(scenario=scen, agent=TooManyEventsAgent(), run_id="run-max")
        self.assertEqual(run.status, RunStatus.FAILED)
        checks = run.metadata["post_execution_checks"]
        self.assertIn("post_execution_max_steps_exceeded", checks["violations"])

    def test_post_execution_timeout_exceeded(self) -> None:
        scen = Scenario(
            id="scen-time",
            name="n",
            description="d",
            task="t",
            max_steps=10,
            timeout_seconds=0.001,
        )
        runner = BasicRunner()
        run = runner.run(scenario=scen, agent=SlowAgent(), run_id="run-time")
        self.assertEqual(run.status, RunStatus.TIMEOUT)
        checks = run.metadata["post_execution_checks"]
        self.assertEqual(checks["mode"], "post_execution_only")

    def test_snapshot_captured(self) -> None:
        runner = BasicRunner()
        run = runner.run(scenario=self.scenario, agent=SampleAgent(), run_id="run-snap")
        self.assertEqual(run.scenario_snapshot["id"], self.scenario.id)
        self.assertEqual(run.scenario_snapshot["metadata"]["expected_output"], "Hello, world!")


if __name__ == "__main__":
    unittest.main()
