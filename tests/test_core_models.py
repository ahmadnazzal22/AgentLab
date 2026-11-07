"""Unit tests for AgentLab core data models."""

import os
import sys
import unittest

# Ensure the 'src' directory is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from agentlab.core.models import (
    Event,
    EventType,
    Result,
    Run,
    RunStatus,
    Scenario,
    Score,
)


class TestScenarioModel(unittest.TestCase):
    """Tests for the Scenario dataclass."""

    def test_valid_scenario_creation_and_defaults(self) -> None:
        scenario = Scenario(
            id="scen_001",
            name="Simple Math",
            description="Tests agent math capability",
            task="Calculate 2 + 2",
        )
        self.assertEqual(scenario.id, "scen_001")
        self.assertEqual(scenario.name, "Simple Math")
        self.assertEqual(scenario.task, "Calculate 2 + 2")
        self.assertEqual(scenario.allowed_tools, [])
        self.assertEqual(scenario.max_steps, 10)
        self.assertEqual(scenario.timeout_seconds, 30.0)
        self.assertEqual(scenario.metadata, {})

    def test_invalid_max_steps(self) -> None:
        with self.assertRaises(ValueError):
            Scenario(
                id="scen_bad_steps",
                name="Bad Steps",
                description="desc",
                task="task",
                max_steps=0,
            )
        with self.assertRaises(ValueError):
            Scenario(
                id="scen_neg_steps",
                name="Negative Steps",
                description="desc",
                task="task",
                max_steps=-5,
            )

    def test_invalid_timeout(self) -> None:
        with self.assertRaises(ValueError):
            Scenario(
                id="scen_bad_timeout",
                name="Zero Timeout",
                description="desc",
                task="task",
                timeout_seconds=0.0,
            )
        with self.assertRaises(ValueError):
            Scenario(
                id="scen_neg_timeout",
                name="Negative Timeout",
                description="desc",
                task="task",
                timeout_seconds=-10.0,
            )

    def test_nan_and_infinity_timeout_rejected(self) -> None:
        for bad_val in [float("nan"), float("inf"), float("-inf")]:
            with self.assertRaises(ValueError, msg=f"Should reject timeout value: {bad_val}"):
                Scenario(
                    id="scen_non_finite",
                    name="Non Finite Timeout",
                    description="desc",
                    task="task",
                    timeout_seconds=bad_val,
                )

    def test_bool_max_steps_and_timeout_rejected(self) -> None:
        # Booleans subclass int in Python, so max_steps=True would pass isinstance(val, int)
        # without explicit guard. Both must be rejected.
        with self.assertRaises(ValueError):
            Scenario(
                id="scen_bool_steps",
                name="Bool Steps",
                description="desc",
                task="task",
                max_steps=True,  # type: ignore[arg-type]
            )
        with self.assertRaises(ValueError):
            Scenario(
                id="scen_bool_steps_false",
                name="Bool Steps False",
                description="desc",
                task="task",
                max_steps=False,  # type: ignore[arg-type]
            )
        with self.assertRaises(ValueError):
            Scenario(
                id="scen_bool_timeout",
                name="Bool Timeout",
                description="desc",
                task="task",
                timeout_seconds=True,  # type: ignore[arg-type]
            )

    def test_empty_id_or_name_or_task(self) -> None:
        with self.assertRaises(ValueError):
            Scenario(id="", name="Name", description="desc", task="task")
        with self.assertRaises(ValueError):
            Scenario(id="id", name="", description="desc", task="task")
        with self.assertRaises(ValueError):
            Scenario(id="id", name="Name", description="desc", task="")

    def test_scenario_serialization_round_trip(self) -> None:
        original = Scenario(
            id="scen_weather",
            name="Weather Lookup",
            description="Check weather tool",
            task="What is the weather in London?",
            allowed_tools=["weather_api"],
            max_steps=5,
            timeout_seconds=15.5,
            metadata={"category": "tools", "level": 1},
        )
        as_dict = original.to_dict()
        reconstructed = Scenario.from_dict(as_dict)
        self.assertEqual(original.id, reconstructed.id)
        self.assertEqual(original.name, reconstructed.name)
        self.assertEqual(original.description, reconstructed.description)
        self.assertEqual(original.task, reconstructed.task)
        self.assertEqual(original.allowed_tools, reconstructed.allowed_tools)
        self.assertEqual(original.max_steps, reconstructed.max_steps)
        self.assertEqual(original.timeout_seconds, reconstructed.timeout_seconds)
        self.assertEqual(original.metadata, reconstructed.metadata)

    def test_mutable_defaults_isolation(self) -> None:
        scen1 = Scenario(id="s1", name="N1", description="D1", task="T1")
        scen2 = Scenario(id="s2", name="N2", description="D2", task="T2")
        scen1.allowed_tools.append("new_tool")
        scen1.metadata["key"] = "val"
        self.assertNotIn("new_tool", scen2.allowed_tools)
        self.assertNotIn("key", scen2.metadata)

    def test_scenario_allowed_tools_must_be_list(self) -> None:
        for bad in ["not-a-list", ("a", "b"), {"a"}, None]:
            with self.assertRaises(ValueError):
                Scenario(id="s", name="n", description="d", task="t", allowed_tools=bad)  # type: ignore[arg-type]

    def test_scenario_allowed_tools_elements_must_be_strings(self) -> None:
        for bad_list in [[123], [None], [True], ["ok", 5]]:
            with self.assertRaises(ValueError):
                Scenario(id="s", name="n", description="d", task="t", allowed_tools=bad_list)  # type: ignore[arg-type]

    def test_scenario_allowed_tools_accepts_empty_and_strings(self) -> None:
        scen = Scenario(id="s", name="n", description="d", task="t", allowed_tools=[])
        self.assertEqual(scen.allowed_tools, [])
        scen2 = Scenario(id="s2", name="n", description="d", task="t", allowed_tools=["search", "calc"])
        self.assertEqual(scen2.allowed_tools, ["search", "calc"])


class TestEventModel(unittest.TestCase):
    """Tests for Event and EventType."""

    def test_valid_event_creation(self) -> None:
        event = Event(
            id="evt_001",
            timestamp="2026-11-03T23:30:00Z",
            type=EventType.TOOL_CALL,
            content={"tool": "search", "query": "hello"},
        )
        self.assertEqual(event.id, "evt_001")
        self.assertEqual(event.type, EventType.TOOL_CALL)
        self.assertEqual(event.content["tool"], "search")

    def test_string_type_converted_to_event_type(self) -> None:
        event = Event(
            id="evt_002",
            timestamp="2026-11-03T23:30:00+03:00",
            type="agent_message",  # type: ignore[arg-type]
            content={"message": "ok"},
        )
        self.assertEqual(event.type, EventType.AGENT_MESSAGE)

    def test_invalid_event_type(self) -> None:
        with self.assertRaises(ValueError):
            Event(
                id="evt_003",
                timestamp="2026-11-03T23:30:00Z",
                type="unknown_event_type",  # type: ignore[arg-type]
            )

    def test_timezone_naive_timestamp_rejected(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            Event(
                id="evt_naive",
                timestamp="2026-11-03T23:30:00",  # No timezone
                type=EventType.SYSTEM,
            )
        self.assertIn("timezone-aware", str(ctx.exception))

    def test_malformed_timestamp_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Event(
                id="evt_malformed",
                timestamp="not-a-date",
                type=EventType.SYSTEM,
            )

    def test_event_serialization_round_trip(self) -> None:
        original = Event(
            id="evt_100",
            timestamp="2026-11-03T20:15:30.123456+00:00",
            type=EventType.ERROR,
            content={"error_code": 404, "details": "not found"},
            metadata={"step": 2},
        )
        as_dict = original.to_dict()
        reconstructed = Event.from_dict(as_dict)
        self.assertEqual(original.id, reconstructed.id)
        self.assertEqual(original.timestamp, reconstructed.timestamp)
        self.assertEqual(original.type, reconstructed.type)
        self.assertEqual(original.content, reconstructed.content)
        self.assertEqual(original.metadata, reconstructed.metadata)


class TestRunModel(unittest.TestCase):
    """Tests for Run and RunStatus."""

    def setUp(self) -> None:
        self.scenario = Scenario(
            id="scen_math",
            name="Math Test",
            description="Add numbers",
            task="Add 1 and 2",
            allowed_tools=["calculator"],
        )

    def test_run_creation_and_defaults(self) -> None:
        run = Run(
            id="run_001",
            scenario_id="scen_math",
            agent_id="mock-agent-1",
            started_at="2026-11-03T23:00:00Z",
        )
        self.assertEqual(run.id, "run_001")
        self.assertEqual(run.scenario_id, "scen_math")
        self.assertEqual(run.agent_id, "mock-agent-1")
        self.assertEqual(run.status, RunStatus.RUNNING)
        self.assertIsNone(run.ended_at)
        self.assertEqual(run.events, [])

    def test_run_create_factory_captures_snapshot(self) -> None:
        run = Run.create(
            id="run_factory_01",
            scenario=self.scenario,
            agent_id="test_agent",
            started_at="2026-11-03T23:00:00Z",
        )
        self.assertEqual(run.scenario_id, self.scenario.id)
        self.assertEqual(run.scenario_snapshot, self.scenario.to_dict())

    def test_run_scenario_snapshot_deep_isolation(self) -> None:
        """Modifying the original Scenario after Run creation must not modify run.scenario_snapshot."""
        scen = Scenario(
            id="scen_deep",
            name="Deep Test",
            description="desc",
            task="task",
            allowed_tools=["tool_a"],
            metadata={"nested": {"counter": 1, "items": ["x", "y"]}},
        )
        run = Run.create(
            id="run_deep",
            scenario=scen,
            agent_id="agent_deep",
            started_at="2026-11-03T23:00:00Z",
        )
        # Deeply mutate the original scenario
        scen.allowed_tools.append("tool_b")
        scen.metadata["nested"]["counter"] = 999
        scen.metadata["nested"]["items"].append("z")

        # Verify run.scenario_snapshot was NOT affected
        self.assertEqual(run.scenario_snapshot["allowed_tools"], ["tool_a"])
        self.assertEqual(run.scenario_snapshot["metadata"]["nested"]["counter"], 1)
        self.assertEqual(run.scenario_snapshot["metadata"]["nested"]["items"], ["x", "y"])

    def test_run_direct_construction_mutable_isolation(self) -> None:
        snapshot = {"nested": {"count": 1}}
        events = []
        metadata = {"info": {"x": 1}}
        run = Run(id="r1", scenario_id="s1", agent_id="a1", started_at="2026-11-03T23:00:00Z", scenario_snapshot=snapshot, events=events, metadata=metadata)
        snapshot["nested"]["count"] = 999
        metadata["info"]["x"] = 555
        self.assertEqual(run.scenario_snapshot["nested"]["count"], 1)
        self.assertEqual(run.metadata["info"]["x"], 1)

    def test_run_field_type_validation(self) -> None:
        with self.assertRaises(ValueError):
            Run(id="r1", scenario_id="s1", agent_id="a1", started_at="2026-11-03T23:00:00Z", scenario_snapshot="x")  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            Run(id="r1", scenario_id="s1", agent_id="a1", started_at="2026-11-03T23:00:00Z", events=[object()])  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            Run(id="r1", scenario_id="s1", agent_id="a1", started_at="2026-11-03T23:00:00Z", metadata="x")  # type: ignore[arg-type]

    def test_safe_agent_id_validation(self) -> None:
        # Valid agent IDs
        valid_ids = ["agent1", "mock-agent-v2", "TEST_AGENT_007", "a"]
        for agent_id in valid_ids:
            run = Run(
                id="run_valid",
                scenario_id="s1",
                agent_id=agent_id,
                started_at="2026-11-03T23:00:00Z",
            )
            self.assertEqual(run.agent_id, agent_id)

        # Unsafe agent IDs (shell commands, paths, spaces, metacharacters)
        unsafe_ids = [
            "rm -rf /",
            "agent; cat /etc/passwd",
            "agent with spaces",
            "../agent/path",
            "agent&eval",
            "agent|pipe",
            "agent$VAR",
            "",
            "agent\n",
        ]
        for unsafe_id in unsafe_ids:
            with self.assertRaises(ValueError, msg=f"Should reject unsafe agent_id: {unsafe_id}"):
                Run(
                    id="run_unsafe",
                    scenario_id="s1",
                    agent_id=unsafe_id,
                    started_at="2026-11-03T23:00:00Z",
                )

    def test_identifier_validation_strict(self) -> None:
        with self.assertRaises(ValueError):
            Scenario(id="../bad", name="n", description="d", task="t")
        with self.assertRaises(ValueError):
            Scenario(id="bad/id", name="n", description="d", task="t")
        with self.assertRaises(ValueError):
            Run(id="r\n", scenario_id="s1", agent_id="a1", started_at="2026-11-03T23:00:00Z")
        long_id = "a" * 65
        with self.assertRaises(ValueError):
            Scenario(id=long_id, name="n", description="d", task="t")

    def test_add_event(self) -> None:
        run = Run(
            id="run_with_events",
            scenario_id="s1",
            agent_id="bot1",
            started_at="2026-11-03T23:00:00Z",
        )
        evt = Event(
            id="e1",
            timestamp="2026-11-03T23:01:00Z",
            type=EventType.AGENT_MESSAGE,
            content={"text": "hello"},
        )
        run.add_event(evt)
        self.assertEqual(len(run.events), 1)
        self.assertEqual(run.events[0].id, "e1")

        with self.assertRaises(TypeError):
            run.add_event("not_an_event")  # type: ignore[arg-type]

    def test_run_nested_serialization_round_trip(self) -> None:
        run = Run.create(
            id="run_full",
            scenario=self.scenario,
            agent_id="verified-agent",
            started_at="2026-11-03T23:00:00Z",
        )
        run.status = RunStatus.COMPLETED
        run.ended_at = "2026-11-03T23:05:00Z"
        run.add_event(
            Event(
                id="e1",
                timestamp="2026-11-03T23:01:00Z",
                type=EventType.TOOL_CALL,
                content={"tool": "calc"},
            )
        )
        run.add_event(
            Event(
                id="e2",
                timestamp="2026-11-03T23:02:00Z",
                type=EventType.TOOL_RESULT,
                content={"result": 3},
            )
        )

        as_dict = run.to_dict()
        reconstructed = Run.from_dict(as_dict)

        self.assertEqual(run.id, reconstructed.id)
        self.assertEqual(run.scenario_id, reconstructed.scenario_id)
        self.assertEqual(run.agent_id, reconstructed.agent_id)
        self.assertEqual(run.status, reconstructed.status)
        self.assertEqual(run.scenario_snapshot, reconstructed.scenario_snapshot)
        self.assertEqual(len(reconstructed.events), 2)
        self.assertEqual(reconstructed.events[0].id, "e1")
        self.assertEqual(reconstructed.events[0].type, EventType.TOOL_CALL)
        self.assertEqual(reconstructed.events[1].id, "e2")
        self.assertEqual(reconstructed.events[1].type, EventType.TOOL_RESULT)


class TestScoreModel(unittest.TestCase):
    """Tests for the Score dataclass."""

    def test_valid_score(self) -> None:
        score = Score(
            evaluator_name="TaskCompletion",
            passed=True,
            value=0.95,
            reason="Completed task with high accuracy",
            evidence_event_ids=["e1", "e2"],
        )
        self.assertEqual(score.evaluator_name, "TaskCompletion")
        self.assertTrue(score.passed)
        self.assertEqual(score.value, 0.95)
        self.assertEqual(score.evidence_event_ids, ["e1", "e2"])

    def test_score_boundary_values(self) -> None:
        score_zero = Score(evaluator_name="E1", passed=False, value=0.0, reason="zero")
        self.assertEqual(score_zero.value, 0.0)

        score_one = Score(evaluator_name="E2", passed=True, value=1.0, reason="one")
        self.assertEqual(score_one.value, 1.0)

    def test_score_value_out_of_bounds(self) -> None:
        with self.assertRaises(ValueError):
            Score(evaluator_name="E", passed=False, value=-0.01, reason="negative")
        with self.assertRaises(ValueError):
            Score(evaluator_name="E", passed=True, value=1.01, reason="too high")

    def test_score_non_finite_and_bool_rejected(self) -> None:
        for bad_val in [float("nan"), float("inf"), float("-inf"), True, False]:
            with self.assertRaises(ValueError, msg=f"Should reject score value: {bad_val}"):
                Score(evaluator_name="E", passed=True, value=bad_val, reason="bad")  # type: ignore[arg-type]

    def test_score_serialization_round_trip(self) -> None:
        score = Score(
            evaluator_name="ToolSafety",
            passed=True,
            value=1.0,
            reason="No unauthorized tools called",
            evidence_event_ids=["e1"],
            metadata={"strict": True},
        )
        as_dict = score.to_dict()
        reconstructed = Score.from_dict(as_dict)
        self.assertEqual(score.evaluator_name, reconstructed.evaluator_name)
        self.assertEqual(score.passed, reconstructed.passed)
        self.assertEqual(score.value, reconstructed.value)
        self.assertEqual(score.reason, reconstructed.reason)
        self.assertEqual(score.evidence_event_ids, reconstructed.evidence_event_ids)
        self.assertEqual(score.metadata, reconstructed.metadata)

    def test_score_from_dict_rejects_string_false(self) -> None:
        with self.assertRaises(ValueError):
            Score.from_dict(
                {
                    "evaluator_name": "E",
                    "passed": "false",
                    "value": 0.5,
                    "reason": "bad",
                }
            )

    def test_score_from_dict_rejects_string_true(self) -> None:
        with self.assertRaises(ValueError):
            Score.from_dict(
                {
                    "evaluator_name": "E",
                    "passed": "true",
                    "value": 0.5,
                    "reason": "bad",
                }
            )

    def test_score_from_dict_rejects_string_zero_one(self) -> None:
        for bad in ["0", "1"]:
            with self.assertRaises(ValueError):
                Score.from_dict(
                    {
                        "evaluator_name": "E",
                        "passed": bad,
                        "value": 0.5,
                        "reason": "bad",
                    }
                )

    def test_score_from_dict_rejects_int_passed(self) -> None:
        for bad in [0, 1]:
            with self.assertRaises(ValueError):
                Score.from_dict(
                    {
                        "evaluator_name": "E",
                        "passed": bad,
                        "value": 0.5,
                        "reason": "bad",
                    }
                )

    def test_score_from_dict_rejects_bool_value(self) -> None:
        for bad in [True, False]:
            with self.assertRaises(ValueError):
                Score.from_dict(
                    {
                        "evaluator_name": "E",
                        "passed": True,
                        "value": bad,
                        "reason": "bad",
                    }
                )

    def test_score_from_dict_rejects_string_value(self) -> None:
        with self.assertRaises(ValueError):
            Score.from_dict(
                {"evaluator_name": "E", "passed": True, "value": "0.5", "reason": "bad"}
            )

    def test_score_from_dict_accepts_bool_true_false(self) -> None:
        s1 = Score.from_dict(
            {"evaluator_name": "E1", "passed": True, "value": 1.0, "reason": "ok"}
        )
        self.assertTrue(s1.passed)
        s2 = Score.from_dict(
            {"evaluator_name": "E2", "passed": False, "value": 0.0, "reason": "bad"}
        )
        self.assertFalse(s2.passed)

    def test_score_field_type_validation(self) -> None:
        with self.assertRaises(ValueError):
            Score(evaluator_name="E", passed=True, value=0.5, reason="ok", evidence_event_ids="e1")  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            Score(evaluator_name="E", passed=True, value=0.5, reason="ok", evidence_event_ids=[123])  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            Score(evaluator_name="E", passed=True, value=0.5, reason="ok", metadata="x")  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            Score(evaluator_name="E", passed=True, value=0.5, reason=None)  # type: ignore[arg-type]


class TestResultModel(unittest.TestCase):
    """Tests for the Result dataclass and computed overall_passed."""

    def test_computed_overall_passed_empty_scores(self) -> None:
        result = Result(
            id="res_001",
            run_id="run_001",
            scenario_id="scen_001",
            created_at="2026-11-03T23:30:00Z",
        )
        # Empty scores must evaluate to False
        self.assertFalse(result.overall_passed)

    def test_computed_overall_passed_all_pass(self) -> None:
        result = Result(
            id="res_002",
            run_id="run_001",
            scenario_id="scen_001",
            created_at="2026-11-03T23:30:00Z",
        )
        result.add_score(Score(evaluator_name="E1", passed=True, value=1.0, reason="ok"))
        result.add_score(Score(evaluator_name="E2", passed=True, value=0.9, reason="ok"))
        self.assertTrue(result.overall_passed)

    def test_computed_overall_passed_one_failure(self) -> None:
        result = Result(
            id="res_003",
            run_id="run_001",
            scenario_id="scen_001",
            created_at="2026-11-03T23:30:00Z",
        )
        result.add_score(Score(evaluator_name="E1", passed=True, value=1.0, reason="ok"))
        result.add_score(Score(evaluator_name="E2", passed=False, value=0.2, reason="failed"))
        self.assertFalse(result.overall_passed)

    def test_tamper_resistance_on_deserialization(self) -> None:
        # If external data claims overall_passed=True while containing a failed score,
        # Result must compute overall_passed dynamically as False!
        tampered_data = {
            "id": "res_tampered",
            "run_id": "run_001",
            "scenario_id": "scen_001",
            "created_at": "2026-11-03T23:30:00Z",
            "overall_passed": True,  # Tampered claim
            "scores": [
                {
                    "evaluator_name": "E1",
                    "passed": False,  # Actual failure
                    "value": 0.0,
                    "reason": "Security violation",
                    "evidence_event_ids": [],
                    "metadata": {},
                }
            ],
            "metrics": {},
        }
        result = Result.from_dict(tampered_data)
        self.assertFalse(result.overall_passed)

    def test_result_nested_serialization_round_trip(self) -> None:
        result = Result(
            id="res_roundtrip",
            run_id="run_123",
            scenario_id="scen_456",
            created_at="2026-11-03T23:45:00+03:00",
            metrics={"duration_seconds": 12.3, "total_steps": 4},
        )
        result.add_score(
            Score(
                evaluator_name="Accuracy",
                passed=True,
                value=0.98,
                reason="Accurate answer",
                evidence_event_ids=["e3"],
            )
        )
        as_dict = result.to_dict()
        self.assertTrue(as_dict["overall_passed"])

        reconstructed = Result.from_dict(as_dict)
        self.assertEqual(result.id, reconstructed.id)
        self.assertEqual(result.run_id, reconstructed.run_id)
        self.assertEqual(result.scenario_id, reconstructed.scenario_id)
        self.assertEqual(result.created_at, reconstructed.created_at)
        self.assertEqual(result.metrics, reconstructed.metrics)
        self.assertEqual(len(reconstructed.scores), 1)
        self.assertEqual(reconstructed.scores[0].evaluator_name, "Accuracy")
        self.assertTrue(reconstructed.overall_passed)

    def test_result_deep_copy_isolation(self) -> None:
        """Nested dicts/lists in Result.metrics and Score.metadata must be independently copied."""
        result = Result(
            id="res_deep",
            run_id="run_deep",
            scenario_id="scen_deep",
            created_at="2026-11-03T23:30:00Z",
            metrics={"nested": {"count": 1, "items": ["a", "b"]}},
        )
        score = Score(
            evaluator_name="DeepTest",
            passed=True,
            value=0.9,
            reason="ok",
            evidence_event_ids=["e1"],
            metadata={"details": {"flags": ["x"]}},
        )
        result.add_score(score)

        as_dict = result.to_dict()
        # Mutate the serialized copies
        as_dict["metrics"]["nested"]["count"] = 999
        as_dict["metrics"]["nested"]["items"].append("c")
        as_dict["scores"][0]["metadata"]["details"]["flags"].append("y")
        as_dict["scores"][0]["evidence_event_ids"].append("e2")

        # Original result must remain unchanged
        self.assertEqual(result.metrics["nested"]["count"], 1)
        self.assertEqual(result.metrics["nested"]["items"], ["a", "b"])
        self.assertEqual(result.scores[0].metadata["details"]["flags"], ["x"])
        self.assertEqual(result.scores[0].evidence_event_ids, ["e1"])

        # Mutating original must not affect deserialized copies
        reconstructed = Result.from_dict(as_dict)
        result.metrics["nested"]["count"] = 555
        result.metrics["nested"]["items"].append("z")
        reconstructed.scores[0].metadata["details"]["flags"].append("mutated")
        reconstructed.scores[0].evidence_event_ids.append("e3")
        self.assertEqual(as_dict["metrics"]["nested"]["count"], 999)
        self.assertEqual(as_dict["metrics"]["nested"]["items"], ["a", "b", "c"])
        self.assertEqual(reconstructed.scores[0].metadata["details"]["flags"], ["x", "y", "mutated"])

    def test_result_direct_construction_mutable_isolation(self) -> None:
        metrics = {"nested": {"count": 1}}
        scores = []
        result = Result(id="res_c", run_id="r1", scenario_id="s1", created_at="2026-11-03T23:30:00Z", scores=scores, metrics=metrics)
        metrics["nested"]["count"] = 999
        self.assertEqual(result.metrics["nested"]["count"], 1)

    def test_result_scores_objects_not_shared(self) -> None:
        score = Score(evaluator_name="E", passed=True, value=1.0, reason="ok")
        result = Result(id="res_s", run_id="r1", scenario_id="s1", created_at="2026-11-03T23:30:00Z", scores=[score])
        score.passed = False  # type: ignore[misc]
        score.value = 0.0  # type: ignore[misc]
        self.assertTrue(result.scores[0].passed)
        self.assertEqual(result.scores[0].value, 1.0)
        self.assertTrue(result.overall_passed)

    def test_result_field_type_validation(self) -> None:
        with self.assertRaises(ValueError):
            Result(id="r1", run_id="r2", scenario_id="s1", created_at="2026-11-03T23:30:00Z", scores=[object()])  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            Result(id="r1", run_id="r2", scenario_id="s1", created_at="2026-11-03T23:30:00Z", metrics="x")  # type: ignore[arg-type]


class TestEventDeepCopy(unittest.TestCase):
    """Deep copy isolation tests for Event."""

    def test_event_deep_copy_isolation(self) -> None:
        """Nested dicts/lists in Event.content and Event.metadata must be independently copied."""
        event = Event(
            id="evt_deep",
            timestamp="2026-11-03T23:30:00Z",
            type=EventType.TOOL_CALL,
            content={"payload": {"items": [1, 2], "data": {"nested": True}}},
            metadata={"trace": {"steps": ["s1"], "info": {"id": 123}}},
        )

        as_dict = event.to_dict()
        # Mutate serialized copies
        as_dict["content"]["payload"]["items"].append(3)
        as_dict["content"]["payload"]["data"]["nested"] = False
        as_dict["metadata"]["trace"]["steps"].append("s2")

        # Original must remain unchanged
        self.assertEqual(event.content["payload"]["items"], [1, 2])
        self.assertTrue(event.content["payload"]["data"]["nested"])
        self.assertEqual(event.metadata["trace"]["steps"], ["s1"])

        # Mutating original must not affect deserialized copies
        reconstructed = Event.from_dict(as_dict)
        event.content["payload"]["items"].append(99)
        reconstructed.metadata["trace"]["steps"].append("s3")
        self.assertEqual(as_dict["content"]["payload"]["items"], [1, 2, 3])
        self.assertEqual(reconstructed.metadata["trace"]["steps"], ["s1", "s2", "s3"])

    def test_event_direct_construction_mutable_isolation(self) -> None:
        content = {"payload": {"items": [1]}}
        metadata = {"trace": {"steps": ["s1"]}}
        event = Event(id="evt_c", timestamp="2026-11-03T23:30:00Z", type=EventType.SYSTEM, content=content, metadata=metadata)
        content["payload"]["items"].append(2)
        metadata["trace"]["steps"].append("s2")
        self.assertEqual(event.content["payload"]["items"], [1])
        self.assertEqual(event.metadata["trace"]["steps"], ["s1"])

    def test_event_field_type_validation(self) -> None:
        with self.assertRaises(ValueError):
            Event(id="e1", timestamp="2026-11-03T23:30:00Z", type=EventType.SYSTEM, content="x")  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            Event(id="e1", timestamp="2026-11-03T23:30:00Z", type=EventType.SYSTEM, metadata="x")  # type: ignore[arg-type]


class TestScoreDeepCopy(unittest.TestCase):
    """Deep copy isolation tests for Score."""

    def test_score_deep_copy_isolation(self) -> None:
        """Nested dicts/lists in Score.metadata and evidence_event_ids must be independently copied."""
        score = Score(
            evaluator_name="DeepScore",
            passed=True,
            value=0.8,
            reason="ok",
            evidence_event_ids=["e1", "e2"],
            metadata={"details": {"tags": ["t1"], "config": {"strict": True}}},
        )

        as_dict = score.to_dict()
        # Mutate serialized copies
        as_dict["evidence_event_ids"].append("e3")
        as_dict["metadata"]["details"]["tags"].append("t2")
        as_dict["metadata"]["details"]["config"]["strict"] = False

        # Original must remain unchanged
        self.assertEqual(score.evidence_event_ids, ["e1", "e2"])
        self.assertEqual(score.metadata["details"]["tags"], ["t1"])
        self.assertTrue(score.metadata["details"]["config"]["strict"])

        # Mutating original must not affect deserialized copies
        reconstructed = Score.from_dict(as_dict)
        score.evidence_event_ids.append("e99")
        reconstructed.metadata["details"]["tags"].append("t3")
        self.assertEqual(as_dict["evidence_event_ids"], ["e1", "e2", "e3"])
        self.assertEqual(reconstructed.metadata["details"]["tags"], ["t1", "t2", "t3"])

    def test_score_direct_construction_mutable_isolation(self) -> None:
        evidence = ["e1"]
        metadata = {"details": {"tags": ["t1"]}}
        score = Score(evaluator_name="E", passed=True, value=0.5, reason="ok", evidence_event_ids=evidence, metadata=metadata)
        evidence.append("e2")
        metadata["details"]["tags"].append("t2")
        self.assertEqual(score.evidence_event_ids, ["e1"])
        self.assertEqual(score.metadata["details"]["tags"], ["t1"])


class TestScenarioDeepCopy(unittest.TestCase):
    """Deep copy isolation tests for Scenario."""

    def test_scenario_from_dict_deep_copy(self) -> None:
        """Scenario.from_dict must deep copy nested dicts/lists passed as data."""
        data = {
            "id": "scen_from_dict",
            "name": "From Dict",
            "description": "test",
            "task": "do something",
            "allowed_tools": ["tool1"],
            "max_steps": 5,
            "timeout_seconds": 10.0,
            "metadata": {"nested": {"count": 1, "items": ["a"]}},
        }
        scenario = Scenario.from_dict(data)
        # Mutate original data
        data["allowed_tools"].append("tool2")
        data["metadata"]["nested"]["count"] = 999
        data["metadata"]["nested"]["items"].append("b")

        # Scenario must remain unchanged
        self.assertEqual(scenario.allowed_tools, ["tool1"])
        self.assertEqual(scenario.metadata["nested"]["count"], 1)
        self.assertEqual(scenario.metadata["nested"]["items"], ["a"])

    def test_scenario_from_dict_strict_types(self) -> None:
        base = {"id": "s1", "name": "n", "description": "d", "task": "t"}
        with self.assertRaises(ValueError):
            Scenario.from_dict({**base, "max_steps": 10.9})
        with self.assertRaises(ValueError):
            Scenario.from_dict({**base, "max_steps": "5"})
        with self.assertRaises(ValueError):
            Scenario.from_dict({**base, "max_steps": True})
        with self.assertRaises(ValueError):
            Scenario.from_dict({**base, "timeout_seconds": "30"})
        with self.assertRaises(ValueError):
            Scenario.from_dict({**base, "timeout_seconds": True})

    def test_scenario_to_dict_deep_copy_isolation(self) -> None:
        """Scenario.to_dict must deep copy nested dicts/lists."""
        scenario = Scenario(
            id="scen_deep2",
            name="Deep2",
            description="test",
            task="task",
            allowed_tools=["t1"],
            metadata={"nested": {"items": [1, 2]}},
        )
        as_dict = scenario.to_dict()
        as_dict["allowed_tools"].append("t2")
        as_dict["metadata"]["nested"]["items"].append(3)
        self.assertEqual(scenario.allowed_tools, ["t1"])
        self.assertEqual(scenario.metadata["nested"]["items"], [1, 2])

    def test_scenario_direct_construction_mutable_isolation(self) -> None:
        tools = ["t1"]
        metadata = {"nested": {"count": 1}}
        scenario = Scenario(id="scen_c", name="n", description="d", task="t", allowed_tools=tools, metadata=metadata)
        tools.append("t2")
        metadata["nested"]["count"] = 999
        self.assertEqual(scenario.allowed_tools, ["t1"])
        self.assertEqual(scenario.metadata["nested"]["count"], 1)

    def test_scenario_field_type_validation(self) -> None:
        with self.assertRaises(ValueError):
            Scenario(id="s1", name="n", description="d", task="t", metadata=None)  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            Scenario(id="s1", name="n", description=123, task="t")  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
