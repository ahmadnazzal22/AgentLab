"""M2 prerequisite/gate tests for M1 review requirements (1-5)."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from agentlab.core.config import (
    Config,
    load_config,
    resolve_path_within_storage,
    validate_runs_dir_path,
)
from agentlab.core.models import (
    Event,
    EventType,
    Result,
    Run,
    RunStatus,
    Scenario,
    Score,
    normalize_identifier_for_comparison,
    validate_identifier,
)


class TestIdentifierPolicy(unittest.TestCase):
    """Gate 1: Identifier policy."""

    def test_alphanumeric_start_required(self) -> None:
        for bad in ["_abc", "-abc", ".abc"]:
            with self.assertRaises(ValueError, msg=bad):
                validate_identifier(bad, "id")

    def test_trailing_dot_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_identifier("abc.", "id")
        with self.assertRaises(ValueError):
            Scenario(id="scen1.", name="n", description="d", task="t")

    def test_windows_reserved_names_rejected(self) -> None:
        reserved = ["CON", "con", "NUL", "nul.txt", "COM1", "com9", "LPT1", "AUX", "PRN"]
        for name in reserved:
            with self.assertRaises(ValueError, msg=name):
                validate_identifier(name, "id")
        # Similar but not reserved should be allowed
        validate_identifier("CONSOLE", "id")
        validate_identifier("COM10", "id")

    def test_case_insensitive_duplicate_policy_helper(self) -> None:
        # Case-only difference normalizes to same comparison key (policy support for storage/registry)
        self.assertEqual(
            normalize_identifier_for_comparison("RunA"),
            normalize_identifier_for_comparison("runa"),
        )
        self.assertNotEqual(
            normalize_identifier_for_comparison("RunA"),
            normalize_identifier_for_comparison("RunB"),
        )

    def test_valid_identifiers_still_allowed(self) -> None:
        for ok in ["a", "A1", "scen_001", "run-001", "task.001", "1abc"]:
            self.assertEqual(validate_identifier(ok, "id"), ok)


class TestRunsDirConstraints(unittest.TestCase):
    """Gate 2: Config.runs_dir constraints."""

    def test_rejects_absolute_drive_parent_and_nul(self) -> None:
        bad_paths = [
            "/abs/path",
            "\\\\server\\share",
            "C:\\runs",
            "C:/runs",
            "../runs",
            "runs/../x",
            "runs\x00bad",
        ]
        for bad in bad_paths:
            with self.assertRaises(ValueError, msg=repr(bad)):
                validate_runs_dir_path(bad)
            with self.assertRaises(ValueError, msg=repr(bad)):
                Config(runs_dir=bad)

    def test_accepts_safe_relative_paths(self) -> None:
        for ok in ["runs", "data/runs", "runs_01", "runs.dir"]:
            self.assertEqual(validate_runs_dir_path(ok), ok)
            Config(runs_dir=ok)

    def test_resolve_path_within_storage_on_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "store"
            base.mkdir()
            resolved = resolve_path_within_storage(base, "runs/run1.json")
            self.assertTrue(resolved.is_relative_to(base.resolve()))
            # Containment check: a path that resolves outside must be rejected
            with self.assertRaises(ValueError):
                resolve_path_within_storage(base, "..\\outside.json") if os.name == "nt" else resolve_path_within_storage(base, "../outside.json")


class TestJSONCompatibilityValidation(unittest.TestCase):
    """Gate 3: JSON compatibility validation."""

    def test_rejects_unsupported_values_and_keys(self) -> None:
        with self.assertRaises(ValueError):
            Scenario(id="s1", name="n", description="d", task="t", metadata={"bad": {1, 2}})
        with self.assertRaises(ValueError):
            Event(
                id="e1",
                timestamp="2026-11-07T10:00:00Z",
                type=EventType.SYSTEM,
                content={"bad": b"x"},
            )
        with self.assertRaises(ValueError):
            Score(evaluator_name="E", passed=True, value=1.0, reason="ok", metadata={1: "x"})  # type: ignore[dict-item]

    def test_rejects_non_finite_numbers(self) -> None:
        with self.assertRaises(ValueError):
            Scenario(id="s1", name="n", description="d", task="t", metadata={"x": float("inf")})

    def test_accepts_supported_json_values(self) -> None:
        meta = {"s": "x", "i": 1, "f": 1.5, "b": True, "n": None, "l": [1, "a"], "d": {"k": "v"}}
        scen = Scenario(id="s1", name="n", description="d", task="t", metadata=meta)
        self.assertEqual(scen.metadata["d"]["k"], "v")

    def test_depth_limit(self) -> None:
        deep: dict[str, object] = {}
        cur = deep
        for _ in range(120):
            nxt: dict[str, object] = {}
            cur["x"] = nxt
            cur = nxt
        with self.assertRaises(ValueError):
            Scenario(id="s1", name="n", description="d", task="t", metadata=deep)


class TestFromDictErrorContract(unittest.TestCase):
    """Gate 4: from_dict error contract."""

    def test_non_dict_input_raises_value_error(self) -> None:
        bad_inputs = [None, "x", 1, [], object()]
        for bad in bad_inputs:
            with self.assertRaises(ValueError, msg=repr(bad)):
                Scenario.from_dict(bad)  # type: ignore[arg-type]
            with self.assertRaises(ValueError, msg=repr(bad)):
                Event.from_dict(bad)  # type: ignore[arg-type]
            with self.assertRaises(ValueError, msg=repr(bad)):
                Run.from_dict(bad)  # type: ignore[arg-type]
            with self.assertRaises(ValueError, msg=repr(bad)):
                Score.from_dict(bad)  # type: ignore[arg-type]
            with self.assertRaises(ValueError, msg=repr(bad)):
                Result.from_dict(bad)  # type: ignore[arg-type]

    def test_missing_required_field_has_clear_value_error(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            Scenario.from_dict({"id": "s1", "name": "n", "description": "d"})
        self.assertIn("task", str(ctx.exception).lower())

    def test_wrong_field_type_has_clear_value_error(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            Run.from_dict(
                {
                    "id": "r1",
                    "scenario_id": "s1",
                    "agent_id": "a1",
                    "started_at": "2026-11-07T10:00:00Z",
                    "events": "not-a-list",
                }
            )
        self.assertIn("events", str(ctx.exception))


class TestUnknownKeyRejection(unittest.TestCase):
    """Gate 5: Unknown-key rejection."""

    def test_scenario_rejects_unknown_key(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            Scenario.from_dict(
                {"id": "s1", "name": "n", "description": "d", "task": "t", "extra": 1}
            )
        self.assertIn("unknown", str(ctx.exception).lower())
        self.assertIn("extra", str(ctx.exception))

    def test_event_rejects_unknown_key(self) -> None:
        with self.assertRaises(ValueError):
            Event.from_dict(
                {
                    "id": "e1",
                    "timestamp": "2026-11-07T10:00:00Z",
                    "type": "system",
                    "content": {},
                    "bogus": True,
                }
            )

    def test_run_rejects_unknown_key(self) -> None:
        with self.assertRaises(ValueError):
            Run.from_dict(
                {
                    "id": "r1",
                    "scenario_id": "s1",
                    "agent_id": "a1",
                    "started_at": "2026-11-07T10:00:00Z",
                    "unknown_run_field": 1,
                }
            )

    def test_score_rejects_unknown_key(self) -> None:
        with self.assertRaises(ValueError):
            Score.from_dict(
                {
                    "evaluator_name": "E",
                    "passed": True,
                    "value": 1.0,
                    "reason": "ok",
                    "extra": "x",
                }
            )

    def test_result_ignores_computed_overall_passed_but_rejects_other_unknown(self) -> None:
        # overall_passed is computed/serialized output - explicitly ignored for tamper-safe round-trip
        data = {
            "id": "res1",
            "run_id": "r1",
            "scenario_id": "s1",
            "created_at": "2026-11-07T10:00:00Z",
            "overall_passed": True,
            "scores": [
                {
                    "evaluator_name": "E",
                    "passed": False,
                    "value": 0.0,
                    "reason": "no",
                }
            ],
            "metrics": {},
        }
        res = Result.from_dict(data)
        self.assertFalse(res.overall_passed)
        data["totally_unknown"] = 1
        with self.assertRaises(ValueError):
            Result.from_dict(data)

    def test_load_config_rejects_unknown_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "c.json"
            p.write_text('{"runs_dir": "runs", "not_a_real_setting": 123}', encoding="utf-8")
            with self.assertRaises(ValueError) as ctx:
                load_config(p)
            self.assertIn("unknown", str(ctx.exception).lower())
            self.assertIn("not_a_real_setting", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
