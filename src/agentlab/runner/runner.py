"""Basic Runner for M2.

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
import time
from typing import Any

from agentlab.agents.base import Agent
from agentlab.core.models import Event, EventType, Run, RunStatus, Scenario


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


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
                id=f"{run_id}-sys-start",
                timestamp=_utc_now_iso(),
                type=EventType.SYSTEM,
                content={"message": "run_started", "scenario_id": scenario.id},
            )
        )

        start_perf = time.perf_counter()
        agent_error: Exception | None = None
        returned_events: list[Event] = []
        try:
            returned_events = agent.execute(scenario)
            if not isinstance(returned_events, list):
                raise TypeError(
                    f"Agent.execute must return list[Event], got {type(returned_events).__name__}"
                )
        except Exception as exc:  # noqa: BLE001 - Runner records execution failures honestly
            agent_error = exc
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
        status = RunStatus.COMPLETED
        violations: list[str] = []
        if agent_error is not None:
            status = RunStatus.FAILED
            violations.append(f"agent_error:{type(agent_error).__name__}")
            run.add_event(
                Event(
                    id=f"{run_id}-sys-error",
                    timestamp=_utc_now_iso(),
                    type=EventType.ERROR,
                    content={
                        "message": "agent_execution_error",
                        "error_type": type(agent_error).__name__,
                        "error": str(agent_error),
                    },
                )
            )

        if elapsed > float(scenario.timeout_seconds):
            status = RunStatus.TIMEOUT
            violations.append("post_execution_timeout_exceeded")

        # max_steps interpreted as max agent-returned events for this basic runner (post-execution).
        if len(returned_events) > scenario.max_steps and status != RunStatus.TIMEOUT:
            status = RunStatus.FAILED
            violations.append("post_execution_max_steps_exceeded")

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
            },
        }
        run.add_event(
            Event(
                id=f"{run_id}-sys-end",
                timestamp=_utc_now_iso(),
                type=EventType.SYSTEM,
                content={"message": "run_finished", "status": str(run.status), "violations": violations},
            )
        )
        return run
