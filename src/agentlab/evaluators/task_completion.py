"""Task Completion Evaluator (M2).

Evaluates a saved Run only - no agent re-execution.
Pass criteria:
- Run status is COMPLETED
- Completion evidence in run events matches expected output from scenario metadata/snapshot
  (Scenario.metadata["expected_output"]). No hardcoded expected values.

Conservative evidence rule (audit remediation): a plain text match is counted as completion
evidence only in result-bearing contexts (e.g. TOOL_RESULT content, or AGENT_MESSAGE marked
final / carrying output-result fields). Expected text appearing only in task restatement
(e.g. a starting task message without completion markers) does not prove completion.
"""

from __future__ import annotations

from typing import Any

from agentlab.core.models import Run, RunStatus, Scenario, Score


def _flatten_strings(value: Any) -> list[str]:
    out: list[str] = []
    if isinstance(value, str):
        out.append(value)
    elif isinstance(value, dict):
        for v in value.values():
            out.extend(_flatten_strings(v))
    elif isinstance(value, list):
        for v in value:
            out.extend(_flatten_strings(v))
    return out


def _contains_expected(value: Any, expected: str) -> bool:
    if not expected:
        return False
    return any(expected in s for s in _flatten_strings(value))


def _is_completion_evidence(ev: Any, expected: str) -> bool:
    et = str(getattr(ev, "type", ""))
    content = getattr(ev, "content", {})
    meta = getattr(ev, "metadata", {})
    if not isinstance(content, dict):
        content = {}
    if not isinstance(meta, dict):
        meta = {}

    if et == "tool_result":
        return _contains_expected(content, expected)

    if et == "agent_message":
        if not _contains_expected(content, expected):
            return False
        # Accept final/result-bearing assistant messages; reject bare task restatements.
        if meta.get("final") is True:
            return True
        for key in ("output", "result", "final_output", "completion"):
            if key in content and _contains_expected(content.get(key), expected):
                return True
        return False

    return False


class TaskCompletionEvaluator:
    name = "task_completion"

    def evaluate(self, run: Run, scenario: Scenario | None = None) -> Score:
        if not isinstance(run, Run):
            raise ValueError(f"run must be a Run, got {type(run).__name__}")

        # Resolve expected output from explicit scenario or saved snapshot (no hardcoding).
        expected = None
        if scenario is not None:
            expected = scenario.metadata.get("expected_output")
        elif isinstance(run.scenario_snapshot, dict):
            snap_meta = run.scenario_snapshot.get("metadata", {})
            if isinstance(snap_meta, dict):
                expected = snap_meta.get("expected_output")

        if expected is None:
            return Score(
                evaluator_name=self.name,
                passed=False,
                value=0.0,
                reason="Missing expected_output in scenario/snapshot metadata; cannot verify completion.",
                evidence_event_ids=[],
            )

        if run.status != RunStatus.COMPLETED:
            return Score(
                evaluator_name=self.name,
                passed=False,
                value=0.0,
                reason=f"Run status is {run.status!s}; COMPLETED status is required.",
                evidence_event_ids=[e.id for e in run.events[:5]],
            )

        expected_str = str(expected)
        matched_ids: list[str] = []
        any_text_match_ids: list[str] = []
        for ev in run.events:
            hay = "\n".join(_flatten_strings(ev.content))
            if expected_str and expected_str in hay:
                any_text_match_ids.append(ev.id)
                if _is_completion_evidence(ev, expected_str):
                    matched_ids.append(ev.id)

        if matched_ids:
            return Score(
                evaluator_name=self.name,
                passed=True,
                value=1.0,
                reason=f"Found expected completion evidence in {len(matched_ids)} event(s).",
                evidence_event_ids=matched_ids,
                metadata={"expected_output": expected_str, "source": "scenario" if scenario else "snapshot"},
            )

        if any_text_match_ids:
            return Score(
                evaluator_name=self.name,
                passed=False,
                value=0.0,
                reason=(
                    "Expected output appeared only in non-completion/task-restatement context; "
                    "completion evidence is required."
                ),
                evidence_event_ids=any_text_match_ids,
                metadata={"expected_output": expected_str},
            )

        return Score(
            evaluator_name=self.name,
            passed=False,
            value=0.0,
            reason="Run completed but no event content matched expected_output.",
            evidence_event_ids=[e.id for e in run.events[:10]],
            metadata={"expected_output": expected_str},
        )
