"""Tool Arguments Evaluator (M3).

Evaluates a saved Run only (no agent re-execution).
Pass criteria:
- Run status is COMPLETED.
- Scenario/snapshot metadata provides expected_args (JSON-compatible object, typically dict).
- Evidence shows a TOOL_CALL whose args match expected_args.
  Matching is deterministic structural equality (Python == on normalized dict/list/scalars
  from JSON-compatible event content).
  - If expected_tool is provided, the TOOL_CALL must be for that tool; if that tool is not
    found, evaluation fails and arguments from a different tool are never compared.
  - If expected_tool is not provided, the primary (first) TOOL_CALL is used.
- Fails if no matching TOOL_CALL exists or args differ.
"""

from __future__ import annotations

from typing import Any

from agentlab.core.models import Run, RunStatus, Scenario, Score


def _get_expected(run: Run, scenario: Scenario | None, key: str) -> Any:
    if scenario is not None and isinstance(scenario.metadata, dict) and key in scenario.metadata:
        return scenario.metadata[key]
    snap = run.scenario_snapshot if isinstance(run.scenario_snapshot, dict) else {}
    meta = snap.get("metadata", {}) if isinstance(snap.get("metadata"), dict) else {}
    return meta.get(key)


def _collect_tool_evidence(run: Run) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    calls: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    ids: list[str] = []
    for ev in run.events:
        et = str(ev.type)
        if et == "tool_call" and isinstance(ev.content, dict):
            calls.append({"event_id": ev.id, **ev.content})
            ids.append(ev.id)
        elif et == "tool_result" and isinstance(ev.content, dict):
            results.append({"event_id": ev.id, **ev.content})
            ids.append(ev.id)
    return calls, results, ids


class ToolArgsEvaluator:
    name = "tool_args"

    def evaluate(self, run: Run, scenario: Scenario | None = None) -> Score:
        if not isinstance(run, Run):
            raise ValueError(f"run must be a Run, got {type(run).__name__}")

        expected_args = _get_expected(run, scenario, "expected_args")
        expected_tool = _get_expected(run, scenario, "expected_tool")
        calls, results, all_ids = _collect_tool_evidence(run)

        if run.status != RunStatus.COMPLETED:
            return Score(
                evaluator_name=self.name,
                passed=False,
                value=0.0,
                reason=f"Run status is {run.status}; expected COMPLETED.",
                evidence_event_ids=all_ids,
                metadata={"run_status": str(run.status), "expected_tool": expected_tool},
            )

        if expected_args is None:
            return Score(
                evaluator_name=self.name,
                passed=False,
                value=0.0,
                reason="No expected_args found in scenario metadata or run scenario_snapshot.metadata.",
                evidence_event_ids=all_ids,
                metadata={"expected_tool": expected_tool},
            )

        if not isinstance(expected_args, dict):
            return Score(
                evaluator_name=self.name,
                passed=False,
                value=0.0,
                reason=f"expected_args must be a dict/object, got {type(expected_args).__name__}.",
                evidence_event_ids=all_ids,
                metadata={"expected_tool": expected_tool},
            )

        if not calls:
            return Score(
                evaluator_name=self.name,
                passed=False,
                value=0.0,
                reason="No TOOL_CALL events found in saved Run.",
                evidence_event_ids=all_ids,
                metadata={"expected_tool": expected_tool, "expected_args": expected_args},
            )

        target = None
        if isinstance(expected_tool, str) and expected_tool:
            for c in calls:
                if c.get("tool") == expected_tool:
                    target = c
                    break
            if target is None:
                attempted_tools = [c.get("tool") for c in calls]
                return Score(
                    evaluator_name=self.name,
                    passed=False,
                    value=0.0,
                    reason=(
                        f"Expected tool '{expected_tool}' not found in TOOL_CALL events; "
                        "argument comparison was not performed on a different tool."
                    ),
                    evidence_event_ids=all_ids,
                    metadata={
                        "expected_tool": expected_tool,
                        "expected_args": expected_args,
                        "attempted_tools": attempted_tools,
                    },
                )
        else:
            target = calls[0]

        actual_args = target.get("args")
        evidence = [target["event_id"]]
        call_id = target.get("call_id")
        for r in results:
            if call_id is not None and r.get("call_id") == call_id:
                evidence.append(r["event_id"])
            elif r.get("tool") == target.get("tool") and call_id is None:
                evidence.append(r["event_id"])

        if not isinstance(actual_args, dict):
            return Score(
                evaluator_name=self.name,
                passed=False,
                value=0.0,
                reason=f"TOOL_CALL args must be a dict, got {type(actual_args).__name__}.",
                evidence_event_ids=evidence,
                metadata={"expected_tool": expected_tool, "expected_args": expected_args, "actual_args": actual_args},
            )

        if actual_args == expected_args:
            return Score(
                evaluator_name=self.name,
                passed=True,
                value=1.0,
                reason="Tool args match expected_args.",
                evidence_event_ids=evidence,
                metadata={
                    "expected_tool": expected_tool,
                    "tool": target.get("tool"),
                    "expected_args": expected_args,
                    "actual_args": actual_args,
                },
            )

        return Score(
            evaluator_name=self.name,
            passed=False,
            value=0.0,
            reason=f"Tool args mismatch for '{target.get('tool')}': expected {expected_args!r}, got {actual_args!r}.",
            evidence_event_ids=evidence,
            metadata={
                "expected_tool": expected_tool,
                "tool": target.get("tool"),
                "expected_args": expected_args,
                "actual_args": actual_args,
            },
        )
