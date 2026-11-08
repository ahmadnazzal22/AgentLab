"""Simple text report for evaluation results."""

from __future__ import annotations

from agentlab.core.models import Result, Run, Score


def render_text_report(run: Run, *, score: Score | None = None, result: Result | None = None) -> str:
    lines: list[str] = []
    lines.append("AgentLab Run Report")
    lines.append("=" * 40)
    lines.append(f"Run ID:       {run.id}")
    lines.append(f"Scenario ID:  {run.scenario_id}")
    lines.append(f"Agent ID:     {run.agent_id}")
    lines.append(f"Status:       {run.status}")
    lines.append(f"Started:      {run.started_at}")
    lines.append(f"Ended:        {run.ended_at}")
    lines.append(f"Events:       {len(run.events)}")
    checks = run.metadata.get("post_execution_checks") if isinstance(run.metadata, dict) else None
    if isinstance(checks, dict):
        lines.append(f"Check mode:   {checks.get('mode')}")
        lines.append(f"Violations:   {checks.get('violations')}")
    lines.append("")
    if result is not None:
        lines.append("Result")
        lines.append("-" * 40)
        lines.append(f"Result ID:    {result.id}")
        lines.append(f"Overall:      {'PASS' if result.overall_passed else 'FAIL'}")
        for s in result.scores:
            lines.append(f"- [{'PASS' if s.passed else 'FAIL'}] {s.evaluator_name} value={s.value}: {s.reason}")
            if s.evidence_event_ids:
                lines.append(f"  evidence: {', '.join(s.evidence_event_ids)}")
    elif score is not None:
        lines.append("Evaluation")
        lines.append("-" * 40)
        lines.append(f"Evaluator:    {score.evaluator_name}")
        lines.append(f"Passed:       {score.passed}")
        lines.append(f"Value:        {score.value}")
        lines.append(f"Reason:       {score.reason}")
        if score.evidence_event_ids:
            lines.append(f"Evidence:     {', '.join(score.evidence_event_ids)}")
    else:
        lines.append("No evaluation result provided.")
    return "\n".join(lines) + "\n"
