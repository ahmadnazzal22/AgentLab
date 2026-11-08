"""Basic Runner for M2/M3 (scope-limited).

Responsibilities:
- Own Run lifecycle (create, start/end timestamps, final status).
- Execute an Agent against a Scenario.
- Record agent-returned events via run.add_event() (agent must not mutate Run).
- Perform post-execution checks for max_steps and timeout_seconds.
  These are batch/post-execution checks only; no immediate interruption,
  hard timeout, subprocess isolation, or sandboxing is claimed/implemented.

Non-responsibilities:
- Does not evaluate results (Evaluator is separate).
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import time
from typing import Any

from agentlab.agents.base import Agent
from agentlab.core.models import Event, EventType, Run, RunStatus, Scenario


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _system_event_id(run_id: str, kind: str) -> str:
    """Generate a short, deterministic, policy-valid system event ID.

    Run IDs may be up to MAX_IDENTIFIER_LENGTH (64). Appending fixed suffixes can
    exceed that limit, so system IDs use a bounded hash while preserving traceability
    by storing the full run_id in event content.
    """
    digest = hashlib.sha256(f"{run_id}:{kind}".encode("utf-8")).hexdigest()[:12]
    # kind is one of start/error/end; result is well under 64 chars and matches identifier rules.
    return f"sys-{kind}-{digest}"


class BasicRunner:
    """Runs a scenario with an agent and produces a completed Run record."""

    def run(
        self,
        *,
        scenario: Scenario,
        agent: Agent,
        run_id: str,
        agent_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Run:
        effective_agent_id = agent_id or getattr(agent, "agent_id", "agent")
        run = Run.create(
            id=run_id,
            scenario=scenario,
            agent_id=effective_agent_id,
            started_at=_utc_now_iso(),
            metadata=metadata or {},
        )
        # Runner owns the Run and records all events via run.add_event().
        run.add_event(
            Event(
                id=_system_event_id(run_id, "start"),
                timestamp=_utc_now_iso(),
                type=EventType.SYSTEM,
                content={"message": "run_started", "scenario_id": scenario.id, "run_id": run_id},
            )
        )

        start_perf = time.perf_counter()
        agent_error: Exception | None = None
        returned_events: list[Event] = []
        returned_type_name: str | None = None
        try:
            raw_returned = agent.execute(scenario)
            returned_type_name = type(raw_returned).__name__
            if not isinstance(raw_returned, list):
                returned_events = []
                raise TypeError(
                    f"Agent.execute must return list[Event], got {returned_type_name}"
                )
            returned_events = raw_returned
        except Exception as exc:  # noqa: BLE001 - Runner records execution failures honestly
            agent_error = exc
            if returned_type_name is None:
                returned_type_name = "unknown"
            if not isinstance(returned_events, list):
                returned_events = []
        elapsed = time.perf_counter() - start_perf

        if agent_error is None:
            for i, ev in enumerate(returned_events):
                if not isinstance(ev, Event):
                    agent_error = TypeError(
                        f"Agent returned non-Event at index {i}: {type(ev).__name__}"
                    )
                    break
                try:
                    run.add_event(ev)
                except Exception as exc:  # noqa: BLE001 - runner must finalize Run record
                    agent_error = RuntimeError(
                        f"Failed to record event at index {i}: {type(exc).__name__}: {exc}"
                    )
                    break

        # Post-execution checks only (batch events; no immediate interruption/hard timeout).
        violations: list[str] = []
        if agent_error is not None:
            violations.append(f"agent_error:{type(agent_error).__name__}")
            run.add_event(
                Event(
                    id=_system_event_id(run_id, "error"),
                    timestamp=_utc_now_iso(),
                    type=EventType.ERROR,
                    content={
                        "message": "agent_execution_error",
                        "error_type": type(agent_error).__name__,
                        "error": str(agent_error),
                        "returned_type": returned_type_name,
                        "run_id": run_id,
                    },
                )
            )

        timed_out = elapsed > float(scenario.timeout_seconds)
        max_steps_exceeded = len(returned_events) > scenario.max_steps
        if timed_out:
            violations.append("post_execution_timeout_exceeded")
        if max_steps_exceeded:
            violations.append("post_execution_max_steps_exceeded")

        # Status precedence (post-execution): agent error -> FAILED; timeout -> TIMEOUT;
        # max_steps only -> FAILED; otherwise COMPLETED. Preserve all detected violations.
        if agent_error is not None:
            status = RunStatus.FAILED
        elif timed_out:
            status = RunStatus.TIMEOUT
        elif max_steps_exceeded:
            status = RunStatus.FAILED
        else:
            status = RunStatus.COMPLETED

        run.status = status
        run.ended_at = _utc_now_iso()
        run.metadata = {
            **run.metadata,
            "runner": "BasicRunner",
            "post_execution_checks": {
                "mode": "post_execution_only",
                "elapsed_seconds": elapsed,
                "timeout_seconds": float(scenario.timeout_seconds),
                "agent_events_returned": len(returned_events),
                "max_steps": scenario.max_steps,
                "violations": violations,
                "timed_out": timed_out,
                "max_steps_exceeded": max_steps_exceeded,
            },
        }
        run.add_event(
            Event(
                id=_system_event_id(run_id, "end"),
                timestamp=_utc_now_iso(),
                type=EventType.SYSTEM,
                content={
                    "message": "run_finished",
                    "status": str(run.status),
                    "violations": violations,
                    "run_id": run_id,
                },
            )
        )
        return run
