"""Tool Choice Evaluator (M3).

Evaluates a saved Run only (no agent re-execution).
Pass criteria:
- Run status is COMPLETED.
- Scenario/snapshot metadata provides expected_tool (str).
- Evidence shows the agent attempted the expected tool and it was allowed/executed
  (TOOL_CALL for expected tool with a matching TOOL_RESULT status 'ok').
- Fails if a tool_not_allowed denial occurred for the primary attempt, if the
  attempted tool differs from expected_tool, or if no valid tool attempt evidence exists.
"""

from __future__ import annotations

from typing import Any

from agentlab.core.models import Run, RunStatus, Scenario, Score


def _get_expected_tool(run: Run, scenario: Scenario | None) -> str | None:
    if scenario is not None and isinstance(scenario.metadata, dict):
        val = scenario.metadata.get("expected_tool")
        if isinstance(val, str) and val:
            return val
    snap = run.scenario_snapshot if isinstance(run.scenario_snapshot, dict) else {}
    meta = snap.get("metadata", {}) if isinstance(snap.get("metadata"), dict) else {}
    val = meta.get("expected_tool")
    return val if isinstance(val, str) and val else None


def _tool_events(run: Run) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    calls: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    evidence: list[str] = []
    for ev in run.events:
        et = str(ev.type)
        if et == "tool_call" and isinstance(ev.content, dict):
            calls.append({"event_id": ev.id, **ev.content})
            evidence.append(ev.id)
        elif et == "tool_result" and isinstance(ev.content, dict):
            results.append({"event_id": ev.id, **ev.content})
            evidence.append(ev.id)
    return calls, results, evidence


class ToolChoiceEvaluator:
    name = "tool_choice"

    def evaluate(self, run: Run, scenario: Scenario | None = None) -> Score:
        if not isinstance(run, Run):
            raise ValueError(f"run must be a Run, got {type(run).__name__}")

        expected_tool = _get_expected_tool(run, scenario)
        calls, results, all_tool_evidence = _tool_events(run)

        if run.status != RunStatus.COMPLETED:
            return Score(
                evaluator_name=self.name,
                passed=False,
                value=0.0,
                reason=f"Run status is {run.status}; expected COMPLETED.",
                evidence_event_ids=all_tool_evidence,
                metadata={"run_status": str(run.status), "expected_tool": expected_tool},
            )

        if not expected_tool:
            return Score(
                evaluator_name=self.name,
                passed=False,
                value=0.0,
                reason="No expected_tool found in scenario metadata or run scenario_snapshot.metadata.",
                evidence_event_ids=all_tool_evidence,
                metadata={"run_status": str(run.status)},
            )

        if not calls:
            return Score(
                evaluator_name=self.name,
                passed=False,
                value=0.0,
                reason="No TOOL_CALL events found in saved Run.",
                evidence_event_ids=all_tool_evidence,
                metadata={"expected_tool": expected_tool},
            )

        # Primary attempt = first TOOL_CALL (deterministic agent convention).
        primary = calls[0]
        attempted_tool = primary.get("tool")
        call_id = primary.get("call_id")
        primary_evidence = [primary["event_id"]]
        if call_id is not None:
            matching_results = [r for r in results if r.get("call_id") == call_id]
        else:
            # Legacy/partial events: bind by attempted tool name when no call_id exists.
            matching_results = [r for r in results if r.get("tool") == attempted_tool]
        for r in matching_results:
            primary_evidence.append(r["event_id"])

        # Bind denial relevance to the primary attempt when call_id is available.
        if call_id is not None:
            denied = [
                r for r in matching_results
                if r.get("status") == "denied" and r.get("reason") == "tool_not_allowed"
            ]
        else:
            denied = [
                r for r in results
                if r.get("status") == "denied" and r.get("reason") == "tool_not_allowed"
            ]

        if attempted_tool != expected_tool:
            reason = (
                f"Tool choice failed: attempted '{attempted_tool}', expected '{expected_tool}'."
            )
            if denied:
                reason += " Disallowed tool attempt was denied and not executed."
            return Score(
                evaluator_name=self.name,
                passed=False,
                value=0.0,
                reason=reason,
                evidence_event_ids=primary_evidence,
                metadata={
                    "expected_tool": expected_tool,
                    "attempted_tool": attempted_tool,
                    "denied": bool(denied),
                },
            )

        ok = [r for r in matching_results if r.get("status") == "ok" and r.get("tool") == expected_tool]
        if ok and not any(r.get("status") == "denied" for r in matching_results):
            return Score(
                evaluator_name=self.name,
                passed=True,
                value=1.0,
                reason=f"Tool choice passed: attempted and executed expected tool '{expected_tool}'.",
                evidence_event_ids=primary_evidence,
                metadata={"expected_tool": expected_tool, "attempted_tool": attempted_tool},
            )

        if denied and attempted_tool == expected_tool:
            # Expected tool was denied (should not happen in valid scenario config, but be explicit).
            return Score(
                evaluator_name=self.name,
                passed=False,
                value=0.0,
                reason=f"Expected tool '{expected_tool}' was denied (tool_not_allowed) and not executed.",
                evidence_event_ids=primary_evidence,
                metadata={"expected_tool": expected_tool, "attempted_tool": attempted_tool, "denied": True},
            )

        detail = matching_results[0].get("status") if matching_results else "missing_result"
        return Score(
            evaluator_name=self.name,
            passed=False,
            value=0.0,
            reason=f"Tool choice failed: expected '{expected_tool}' was not executed successfully (result={detail}).",
            evidence_event_ids=primary_evidence,
            metadata={"expected_tool": expected_tool, "attempted_tool": attempted_tool, "result_status": detail},
        )
