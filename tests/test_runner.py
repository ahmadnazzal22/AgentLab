"""Tests for BasicRunner (M2) and audit regressions (P2/P3/P4)."""

import os
import sys
import time
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from agentlab.agents.base import Agent
from agentlab.agents.sample_agent import SampleAgent
from agentlab.core.models import Event, EventType, MAX_IDENTIFIER_LENGTH, RunStatus, Scenario
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


class NoneReturningAgent(Agent):
    def execute(self, scenario: Scenario):
        return None


class IntReturningAgent(Agent):
    def execute(self, scenario: Scenario):
        return 7


class DictReturningAgent(Agent):
    def execute(self, scenario: Scenario):
        return {"not": "a list"}


class SlowTooManyEventsAgent(Agent):
    def execute(self, scenario: Scenario) -> list[Event]:
        time.sleep(0.05)
        return [
            Event(
                id=f"slow-e{i}",
                timestamp="2026-01-01T00:00:00Z",
                type=EventType.AGENT_MESSAGE,
                content={"i": i},
            )
            for i in range(1, 6)
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

    def test_agent_returns_none_produces_failed_run_not_crash(self) -> None:
        runner = BasicRunner()
        run = runner.run(scenario=self.scenario, agent=NoneReturningAgent(), run_id="run-none")
        self.assertEqual(run.status, RunStatus.FAILED)
        self.assertTrue(any(e.type == EventType.ERROR for e in run.events))
        checks = run.metadata["post_execution_checks"]
        self.assertEqual(checks["agent_events_returned"], 0)
        self.assertTrue(any("agent_error:TypeError" == v for v in checks["violations"]))

    def test_agent_returns_int_produces_failed_run_not_crash(self) -> None:
        runner = BasicRunner()
        run = runner.run(scenario=self.scenario, agent=IntReturningAgent(), run_id="run-int")
        self.assertEqual(run.status, RunStatus.FAILED)
        checks = run.metadata["post_execution_checks"]
        self.assertEqual(checks["agent_events_returned"], 0)

    def test_agent_returns_dict_produces_failed_run_not_crash(self) -> None:
        runner = BasicRunner()
        run = runner.run(scenario=self.scenario, agent=DictReturningAgent(), run_id="run-dict")
        self.assertEqual(run.status, RunStatus.FAILED)
        checks = run.metadata["post_execution_checks"]
        self.assertEqual(checks["agent_events_returned"], 0)

    def test_long_valid_run_id_produces_valid_system_event_ids(self) -> None:
        runner = BasicRunner()
        run_id = "r" * MAX_IDENTIFIER_LENGTH  # valid max-length run ID
        run = runner.run(scenario=self.scenario, agent=SampleAgent(), run_id=run_id)
        self.assertEqual(run.id, run_id)
        self.assertIn(run.status, {RunStatus.COMPLETED, RunStatus.TIMEOUT, RunStatus.FAILED})
        messages = [e.content.get("message") for e in run.events if isinstance(e.content, dict)]
        self.assertIn("run_started", messages)
        self.assertIn("run_finished", messages)
        for ev in run.events:
            self.assertLessEqual(len(ev.id), MAX_IDENTIFIER_LENGTH)
            self.assertRegex(ev.id, r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")

    def test_long_valid_run_id_error_path_has_valid_event_ids(self) -> None:
        runner = BasicRunner()
        run_id = "e" * MAX_IDENTIFIER_LENGTH
        run = runner.run(scenario=self.scenario, agent=NoneReturningAgent(), run_id=run_id)
        self.assertEqual(run.status, RunStatus.FAILED)
        messages = [e.content.get("message") for e in run.events if isinstance(e.content, dict)]
        self.assertIn("agent_execution_error", messages)
        for ev in run.events:
            self.assertLessEqual(len(ev.id), MAX_IDENTIFIER_LENGTH)

    def test_timeout_and_max_steps_both_recorded(self) -> None:
        scen = Scenario(
            id="scen-both",
            name="n",
            description="d",
            task="t",
            max_steps=2,
            timeout_seconds=0.001,
        )
        runner = BasicRunner()
        run = runner.run(scenario=scen, agent=SlowTooManyEventsAgent(), run_id="run-both")
        checks = run.metadata["post_execution_checks"]
        self.assertEqual(checks["mode"], "post_execution_only")
        self.assertIn("post_execution_timeout_exceeded", checks["violations"])
        self.assertIn("post_execution_max_steps_exceeded", checks["violations"])
        # Precedence (approved): agent error -> FAILED; timeout -> TIMEOUT; max_steps only -> FAILED.
        self.assertEqual(run.status, RunStatus.TIMEOUT)


if __name__ == "__main__":
    unittest.main()
