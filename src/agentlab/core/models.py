"""Core data models for the AgentLab evaluation platform.

This module defines the fundamental data shapes used across the system:
- EventType and RunStatus: Controlled string enumerations.
- Scenario: The test case specification.
- Event: An atomic recorded interaction during a test run.
- Run: The full execution record of an agent running a scenario.
- Score: An individual evaluator's assessment with supporting evidence.
- Result: The aggregated evaluation outcome and computed overall score.

Rule: core/ depends on nothing else in the project.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
import copy
import math
import re
from typing import Any

# Pattern for safe agent identifiers: alphanumeric characters, underscores, and hyphens only.
# Strictly forbids shell metacharacters, spaces, paths, or command strings.
SAFE_AGENT_ID_REGEX = re.compile(r"^[a-zA-Z0-9_-]+$")
MAX_IDENTIFIER_LENGTH = 64
MAX_JSON_DEPTH = 100

WINDOWS_RESERVED_NAMES: frozenset[str] = frozenset(
    {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{i}" for i in range(1, 10)),
        *(f"LPT{i}" for i in range(1, 10)),
    }
)


def _contains_forbidden_id_chars(value: str) -> bool:
    if "\n" in value or "\r" in value or "\x00" in value:
        return True
    if "/" in value or "\\" in value or ".." in value:
        return True
    return False


def _reserved_name_token(value: str) -> str:
    # Windows device names are reserved regardless of extension (e.g., CON.txt)
    token = value.split(".", 1)[0]
    return token.upper()


def normalize_identifier_for_comparison(value: str) -> str:
    """Normalize an identifier for case-insensitive duplicate checks (storage/policy use)."""
    return value.casefold()


def validate_identifier(value: Any, field_name: str, allow_safe_agent_chars_only: bool = False) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string, got {type(value).__name__}")
    if not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    if len(value) > MAX_IDENTIFIER_LENGTH:
        raise ValueError(f"{field_name} must be at most {MAX_IDENTIFIER_LENGTH} characters")
    if _contains_forbidden_id_chars(value):
        raise ValueError(f"{field_name} contains invalid characters")
    if not value[0].isalnum():
        raise ValueError(f"{field_name} must start with an alphanumeric character")
    if value.endswith("."):
        raise ValueError(f"{field_name} must not end with a dot")
    if allow_safe_agent_chars_only:
        if not re.fullmatch(r"[a-zA-Z0-9_-]+", value):
            raise ValueError(
                f"{field_name} must be a safe identifier containing only letters, numbers, "
                "underscores, or hyphens (raw shell commands and paths are strictly forbidden)"
            )
    else:
        if not re.fullmatch(r"[a-zA-Z0-9_.-]+", value):
            raise ValueError(f"{field_name} contains invalid characters")
    if _reserved_name_token(value) in WINDOWS_RESERVED_NAMES:
        raise ValueError(f"{field_name} uses a reserved Windows device name")
    return value


def validate_json_compatible(value: Any, field_name: str, *, _depth: int = 0) -> None:
    """Validate that a value is JSON-compatible (for metadata/content/metrics fields).

    Rules:
    - string keys in dicts
    - supported JSON values: dict, list, str, int, float (finite), bool, None
    - rejects set/tuple/bytes/custom objects (except accepted via explicit conversion policy: none)
    - rejects NaN/Infinity
    - enforces depth limit
    """
    if _depth > MAX_JSON_DEPTH:
        raise ValueError(f"{field_name} exceeds maximum nesting depth ({MAX_JSON_DEPTH})")
    if value is None:
        return
    if isinstance(value, bool):
        return
    if isinstance(value, int):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"{field_name} contains a non-finite number (NaN/Infinity not allowed)")
        return
    if isinstance(value, str):
        return
    if isinstance(value, list):
        for i, item in enumerate(value):
            validate_json_compatible(item, f"{field_name}[{i}]", _depth=_depth + 1)
        return
    if isinstance(value, dict):
        for k, v in value.items():
            if not isinstance(k, str):
                raise ValueError(f"{field_name} contains a non-string key: {type(k).__name__}")
            validate_json_compatible(v, f"{field_name}.{k}", _depth=_depth + 1)
        return
    if isinstance(value, (set, tuple, bytes, bytearray)):
        raise ValueError(f"{field_name} contains an unsupported JSON type: {type(value).__name__}")
    raise ValueError(f"{field_name} contains an unsupported JSON type: {type(value).__name__}")


def _require_dict(data: Any, context: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError(f"{context} data must be a dictionary, got {type(data).__name__}")
    return data


def _reject_unknown_keys(data: dict[str, Any], allowed: set[str], context: str, *, ignored: set[str] | None = None) -> None:
    ignored = ignored or set()
    unknown = sorted(k for k in data.keys() if k not in allowed and k not in ignored)
    if unknown:
        raise ValueError(f"{context} contains unknown field(s): {', '.join(unknown)}")


def _require_field(data: dict[str, Any], key: str, context: str) -> Any:
    if key not in data:
        raise ValueError(f"{context} is missing required field '{key}'")
    return data[key]


def validate_iso_timestamp(ts: Any, field_name: str) -> None:
    """Validates that a timestamp string is valid ISO 8601 and timezone-aware.

    Args:
        ts: The timestamp string to validate.
        field_name: The name of the field for descriptive error messages.

    Raises:
        ValueError: If ts is not a string, not valid ISO 8601, or is timezone-naive.
    """
    if not isinstance(ts, str):
        raise ValueError(f"{field_name} must be a string, got {type(ts).__name__}")
    if not ts.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    try:
        dt = datetime.fromisoformat(ts)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"{field_name} must be a valid ISO 8601 string: {exc}") from exc
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        raise ValueError(
            f"{field_name} must be timezone-aware (e.g., including 'Z' or a UTC offset like '+00:00')"
        )


class EventType(StrEnum):
    """Controlled set of allowed event types recorded during an agent test run."""

    AGENT_MESSAGE = "agent_message"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    APPROVAL_REQUEST = "approval_request"
    APPROVAL_RESPONSE = "approval_response"
    ERROR = "error"
    SYSTEM = "system"


class RunStatus(StrEnum):
    """Controlled set of execution statuses for a test run."""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass(slots=True, kw_only=True)
class Scenario:
    """Defines a test scenario specification for an AI agent under test."""

    id: str
    name: str
    description: str
    task: str
    allowed_tools: list[str] = field(default_factory=list)
    max_steps: int = 10
    timeout_seconds: float = 30.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validates scenario parameters."""
        validate_identifier(self.id, "Scenario.id")
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Scenario.name must be a non-empty string")
        if not isinstance(self.description, str):
            raise ValueError("Scenario.description must be a string")
        if not isinstance(self.task, str) or not self.task.strip():
            raise ValueError("Scenario.task must be a non-empty string")
        if not isinstance(self.allowed_tools, list):
            raise ValueError(f"Scenario.allowed_tools must be a list, got {type(self.allowed_tools).__name__}")
        for i, tool in enumerate(self.allowed_tools):
            if not isinstance(tool, str):
                raise ValueError(f"Scenario.allowed_tools[{i}] must be a string, got {type(tool).__name__}")
        if not isinstance(self.metadata, dict):
            raise ValueError(f"Scenario.metadata must be a dictionary, got {type(self.metadata).__name__}")
        validate_json_compatible(self.metadata, "Scenario.metadata")
        # Reject booleans explicitly because in Python, bool subclasses int (isinstance(True, int) == True)
        if isinstance(self.max_steps, bool) or not isinstance(self.max_steps, int) or self.max_steps <= 0:
            raise ValueError("Scenario.max_steps must be a positive integer greater than zero (booleans not allowed)")
        if (
            isinstance(self.timeout_seconds, bool)
            or not isinstance(self.timeout_seconds, (int, float))
            or not math.isfinite(self.timeout_seconds)
            or self.timeout_seconds <= 0.0
        ):
            raise ValueError(
                "Scenario.timeout_seconds must be a finite positive number greater than zero (NaN, Infinity, and booleans not allowed)"
            )
        # Deep copy mutable fields to prevent shared references from direct construction
        object.__setattr__(self, "allowed_tools", copy.deepcopy(self.allowed_tools))
        object.__setattr__(self, "metadata", copy.deepcopy(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        """Serializes the Scenario to a JSON-compatible dictionary with deep copies."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "task": self.task,
            "allowed_tools": copy.deepcopy(self.allowed_tools),
            "max_steps": self.max_steps,
            "timeout_seconds": float(self.timeout_seconds),
            "metadata": copy.deepcopy(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Scenario":
        """Deserializes a Scenario from a dictionary."""
        data = _require_dict(data, "Scenario")
        _reject_unknown_keys(
            data,
            {
                "id",
                "name",
                "description",
                "task",
                "allowed_tools",
                "max_steps",
                "timeout_seconds",
                "metadata",
            },
            "Scenario",
        )
        max_steps = data.get("max_steps", 10)
        timeout_seconds = data.get("timeout_seconds", 30.0)
        if isinstance(max_steps, bool) or not isinstance(max_steps, int):
            raise ValueError("Scenario.max_steps must be a positive integer greater than zero (booleans not allowed)")
        if isinstance(timeout_seconds, bool) or isinstance(timeout_seconds, str) or not isinstance(timeout_seconds, (int, float)):
            raise ValueError(
                "Scenario.timeout_seconds must be a finite positive number greater than zero (NaN, Infinity, and booleans not allowed)"
            )
        allowed_tools = data.get("allowed_tools", [])
        if not isinstance(allowed_tools, list):
            raise ValueError(f"Scenario.allowed_tools must be a list, got {type(allowed_tools).__name__}")
        for i, tool in enumerate(allowed_tools):
            if not isinstance(tool, str):
                raise ValueError(f"Scenario.allowed_tools[{i}] must be a string, got {type(tool).__name__}")
        metadata = data.get("metadata", {})
        if not isinstance(metadata, dict):
            raise ValueError(f"Scenario.metadata must be a dictionary, got {type(metadata).__name__}")
        validate_json_compatible(metadata, "Scenario.metadata")
        try:
            return cls(
                id=_require_field(data, "id", "Scenario"),
                name=_require_field(data, "name", "Scenario"),
                description=_require_field(data, "description", "Scenario"),
                task=_require_field(data, "task", "Scenario"),
                allowed_tools=copy.deepcopy(allowed_tools),
                max_steps=max_steps,
                timeout_seconds=timeout_seconds,
                metadata=copy.deepcopy(metadata),
            )
        except KeyError as exc:
            raise ValueError(f"Scenario is missing required field {exc!s}") from exc


@dataclass(slots=True, kw_only=True)
class Event:
    """Represents a single atomic interaction event recorded during an agent test run."""

    id: str
    timestamp: str
    type: EventType
    content: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validates event parameters and formats."""
        validate_identifier(self.id, "Event.id")
        validate_iso_timestamp(self.timestamp, "Event.timestamp")
        if isinstance(self.type, str):
            try:
                self.type = EventType(self.type)
            except ValueError as exc:
                raise ValueError(f"Event.type '{self.type}' is not a valid EventType") from exc
        elif not isinstance(self.type, EventType):
            raise ValueError(f"Event.type must be an EventType instance, got {type(self.type).__name__}")
        if not isinstance(self.content, dict):
            raise ValueError(f"Event.content must be a dictionary, got {type(self.content).__name__}")
        if not isinstance(self.metadata, dict):
            raise ValueError(f"Event.metadata must be a dictionary, got {type(self.metadata).__name__}")
        validate_json_compatible(self.content, "Event.content")
        validate_json_compatible(self.metadata, "Event.metadata")
        object.__setattr__(self, "content", copy.deepcopy(self.content))
        object.__setattr__(self, "metadata", copy.deepcopy(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        """Serializes the Event to a JSON-compatible dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "type": str(self.type),
            "content": copy.deepcopy(self.content),
            "metadata": copy.deepcopy(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Event":
        """Deserializes an Event from a dictionary."""
        data = _require_dict(data, "Event")
        _reject_unknown_keys(data, {"id", "timestamp", "type", "content", "metadata"}, "Event")
        content = data.get("content", {})
        metadata = data.get("metadata", {})
        if not isinstance(content, dict):
            raise ValueError(f"Event.content must be a dictionary, got {type(content).__name__}")
        if not isinstance(metadata, dict):
            raise ValueError(f"Event.metadata must be a dictionary, got {type(metadata).__name__}")
        validate_json_compatible(content, "Event.content")
        validate_json_compatible(metadata, "Event.metadata")
        raw_type = _require_field(data, "type", "Event")
        try:
            event_type = EventType(raw_type)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Event.type is not a valid EventType: {raw_type!r}") from exc
        try:
            return cls(
                id=_require_field(data, "id", "Event"),
                timestamp=_require_field(data, "timestamp", "Event"),
                type=event_type,
                content=copy.deepcopy(content),
                metadata=copy.deepcopy(metadata),
            )
        except KeyError as exc:
            raise ValueError(f"Event is missing required field {exc!s}") from exc


@dataclass(slots=True, kw_only=True)
class Run:
    """Represents the complete execution record of an agent running a scenario."""

    id: str
    scenario_id: str
    agent_id: str
    started_at: str
    ended_at: str | None = None
    status: RunStatus = RunStatus.RUNNING
    scenario_snapshot: dict[str, Any] = field(default_factory=dict)
    events: list[Event] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validates run parameters, security restrictions, and timestamp formats."""
        validate_identifier(self.id, "Run.id")
        validate_identifier(self.scenario_id, "Run.scenario_id")
        validate_identifier(self.agent_id, "Run.agent_id", allow_safe_agent_chars_only=True)
        validate_iso_timestamp(self.started_at, "Run.started_at")
        if self.ended_at is not None:
            validate_iso_timestamp(self.ended_at, "Run.ended_at")
        if isinstance(self.status, str):
            try:
                self.status = RunStatus(self.status)
            except ValueError as exc:
                raise ValueError(f"Run.status '{self.status}' is not a valid RunStatus") from exc
        elif not isinstance(self.status, RunStatus):
            raise ValueError(f"Run.status must be a RunStatus instance, got {type(self.status).__name__}")
        if not isinstance(self.scenario_snapshot, dict):
            raise ValueError(f"Run.scenario_snapshot must be a dictionary, got {type(self.scenario_snapshot).__name__}")
        if not isinstance(self.events, list):
            raise ValueError(f"Run.events must be a list, got {type(self.events).__name__}")
        for i, ev in enumerate(self.events):
            if not isinstance(ev, Event):
                raise ValueError(f"Run.events[{i}] must be an Event instance, got {type(ev).__name__}")
        if not isinstance(self.metadata, dict):
            raise ValueError(f"Run.metadata must be a dictionary, got {type(self.metadata).__name__}")
        validate_json_compatible(self.scenario_snapshot, "Run.scenario_snapshot")
        validate_json_compatible(self.metadata, "Run.metadata")
        object.__setattr__(self, "scenario_snapshot", copy.deepcopy(self.scenario_snapshot))
        object.__setattr__(self, "events", [copy.deepcopy(ev) for ev in self.events])
        object.__setattr__(self, "metadata", copy.deepcopy(self.metadata))

    @classmethod
    def create(
        cls,
        *,
        id: str,
        scenario: Scenario,
        agent_id: str,
        started_at: str,
        metadata: dict[str, Any] | None = None,
    ) -> "Run":
        """Factory helper to create a Run while capturing an independent deep snapshot of the Scenario."""
        return cls(
            id=id,
            scenario_id=scenario.id,
            agent_id=agent_id,
            started_at=started_at,
            scenario_snapshot=copy.deepcopy(scenario.to_dict()),
            metadata=copy.deepcopy(metadata or {}),
        )

    def add_event(self, event: Event) -> None:
        """Appends a new Event to the chronological execution log."""
        if not isinstance(event, Event):
            raise TypeError(f"Expected Event instance, got {type(event).__name__}")
        self.events.append(copy.deepcopy(event))

    def to_dict(self) -> dict[str, Any]:
        """Serializes the Run and all nested events to a JSON-compatible dictionary."""
        return {
            "id": self.id,
            "scenario_id": self.scenario_id,
            "agent_id": self.agent_id,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "status": str(self.status),
            "scenario_snapshot": copy.deepcopy(self.scenario_snapshot),
            "events": [event.to_dict() for event in self.events],
            "metadata": copy.deepcopy(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Run":
        """Deserializes a Run and all nested events from a dictionary."""
        data = _require_dict(data, "Run")
        _reject_unknown_keys(
            data,
            {
                "id",
                "scenario_id",
                "agent_id",
                "started_at",
                "ended_at",
                "status",
                "scenario_snapshot",
                "events",
                "metadata",
            },
            "Run",
        )
        scenario_snapshot = data.get("scenario_snapshot", {})
        events_data = data.get("events", [])
        metadata = data.get("metadata", {})
        if not isinstance(scenario_snapshot, dict):
            raise ValueError(f"Run.scenario_snapshot must be a dictionary, got {type(scenario_snapshot).__name__}")
        if not isinstance(events_data, list):
            raise ValueError(f"Run.events must be a list, got {type(events_data).__name__}")
        if not isinstance(metadata, dict):
            raise ValueError(f"Run.metadata must be a dictionary, got {type(metadata).__name__}")
        validate_json_compatible(scenario_snapshot, "Run.scenario_snapshot")
        validate_json_compatible(metadata, "Run.metadata")
        raw_status = data.get("status", RunStatus.RUNNING)
        try:
            status = RunStatus(raw_status)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Run.status is not a valid RunStatus: {raw_status!r}") from exc
        try:
            return cls(
                id=_require_field(data, "id", "Run"),
                scenario_id=_require_field(data, "scenario_id", "Run"),
                agent_id=_require_field(data, "agent_id", "Run"),
                started_at=_require_field(data, "started_at", "Run"),
                ended_at=data.get("ended_at"),
                status=status,
                scenario_snapshot=copy.deepcopy(scenario_snapshot),
                events=[Event.from_dict(event_dict) for event_dict in events_data],
                metadata=copy.deepcopy(metadata),
            )
        except KeyError as exc:
            raise ValueError(f"Run is missing required field {exc!s}") from exc


@dataclass(slots=True, kw_only=True)
class Score:
    """Represents an individual assessment produced by an evaluator with evidence."""

    evaluator_name: str
    passed: bool
    value: float
    reason: str
    evidence_event_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validates score attributes."""
        if not isinstance(self.evaluator_name, str) or not self.evaluator_name.strip():
            raise ValueError("Score.evaluator_name must be a non-empty string")
        if not isinstance(self.passed, bool):
            raise ValueError("Score.passed must be a boolean (True or False)")
        if (
            isinstance(self.value, bool)
            or not isinstance(self.value, (int, float))
            or not math.isfinite(self.value)
            or not (0.0 <= float(self.value) <= 1.0)
        ):
            raise ValueError(
                f"Score.value must be a finite number between 0.0 and 1.0 inclusive (booleans, NaN, and Infinity not allowed), got {self.value}"
            )
        self.value = float(self.value)
        if not isinstance(self.reason, str):
            raise ValueError("Score.reason must be a string")
        if not isinstance(self.evidence_event_ids, list):
            raise ValueError(f"Score.evidence_event_ids must be a list, got {type(self.evidence_event_ids).__name__}")
        for i, eid in enumerate(self.evidence_event_ids):
            if not isinstance(eid, str):
                raise ValueError(f"Score.evidence_event_ids[{i}] must be a string, got {type(eid).__name__}")
        if not isinstance(self.metadata, dict):
            raise ValueError(f"Score.metadata must be a dictionary, got {type(self.metadata).__name__}")
        validate_json_compatible(self.metadata, "Score.metadata")
        object.__setattr__(self, "evidence_event_ids", copy.deepcopy(self.evidence_event_ids))
        object.__setattr__(self, "metadata", copy.deepcopy(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        """Serializes the Score to a JSON-compatible dictionary."""
        return {
            "evaluator_name": self.evaluator_name,
            "passed": self.passed,
            "value": self.value,
            "reason": self.reason,
            "evidence_event_ids": copy.deepcopy(self.evidence_event_ids),
            "metadata": copy.deepcopy(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Score":
        """Deserializes a Score from a dictionary."""
        data = _require_dict(data, "Score")
        _reject_unknown_keys(
            data,
            {"evaluator_name", "passed", "value", "reason", "evidence_event_ids", "metadata"},
            "Score",
        )
        passed = _require_field(data, "passed", "Score")
        if not isinstance(passed, bool):
            raise ValueError(f"Score.passed must be a boolean (True or False), got {type(passed).__name__}")
        value = _require_field(data, "value", "Score")
        if isinstance(value, bool):
            raise ValueError(
                f"Score.value must be a finite number between 0.0 and 1.0 inclusive (booleans, NaN, and Infinity not allowed), got {value}"
            )
        if isinstance(value, str):
            raise ValueError(
                f"Score.value must be a finite number between 0.0 and 1.0 inclusive (booleans, NaN, and Infinity not allowed), got {value}"
            )
        if not isinstance(value, (int, float)):
            raise ValueError(
                f"Score.value must be a finite number between 0.0 and 1.0 inclusive (booleans, NaN, and Infinity not allowed), got {value}"
            )
        evidence_event_ids = data.get("evidence_event_ids", [])
        if not isinstance(evidence_event_ids, list):
            raise ValueError(f"Score.evidence_event_ids must be a list, got {type(evidence_event_ids).__name__}")
        for i, eid in enumerate(evidence_event_ids):
            if not isinstance(eid, str):
                raise ValueError(f"Score.evidence_event_ids[{i}] must be a string, got {type(eid).__name__}")
        metadata = data.get("metadata", {})
        if not isinstance(metadata, dict):
            raise ValueError(f"Score.metadata must be a dictionary, got {type(metadata).__name__}")
        validate_json_compatible(metadata, "Score.metadata")
        reason = data.get("reason", "")
        if not isinstance(reason, str):
            raise ValueError("Score.reason must be a string")
        try:
            return cls(
                evaluator_name=_require_field(data, "evaluator_name", "Score"),
                passed=passed,
                value=float(value),
                reason=reason,
                evidence_event_ids=copy.deepcopy(evidence_event_ids),
                metadata=copy.deepcopy(metadata),
            )
        except KeyError as exc:
            raise ValueError(f"Score is missing required field {exc!s}") from exc


@dataclass(slots=True, kw_only=True)
class Result:
    """Aggregates all evaluator scores and metrics for a specific test run."""

    id: str
    run_id: str
    scenario_id: str
    created_at: str
    scores: list[Score] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validates result attributes and timestamp format."""
        validate_identifier(self.id, "Result.id")
        validate_identifier(self.run_id, "Result.run_id")
        validate_identifier(self.scenario_id, "Result.scenario_id")
        validate_iso_timestamp(self.created_at, "Result.created_at")
        if not isinstance(self.scores, list):
            raise ValueError(f"Result.scores must be a list, got {type(self.scores).__name__}")
        for i, sc in enumerate(self.scores):
            if not isinstance(sc, Score):
                raise ValueError(f"Result.scores[{i}] must be a Score instance, got {type(sc).__name__}")
        if not isinstance(self.metrics, dict):
            raise ValueError(f"Result.metrics must be a dictionary, got {type(self.metrics).__name__}")
        validate_json_compatible(self.metrics, "Result.metrics")
        object.__setattr__(self, "scores", [copy.deepcopy(sc) for sc in self.scores])
        object.__setattr__(self, "metrics", copy.deepcopy(self.metrics))

    @property
    def overall_passed(self) -> bool:
        """Dynamically computes the overall pass/fail outcome.

        Returns:
            False if scores is empty (no evaluation took place).
            True if and only if every score in self.scores has passed == True.
        """
        if not self.scores:
            return False
        return all(score.passed for score in self.scores)

    def add_score(self, score: Score) -> None:
        """Adds an evaluator Score to the result."""
        if not isinstance(score, Score):
            raise TypeError(f"Expected Score instance, got {type(score).__name__}")
        self.scores.append(copy.deepcopy(score))

    def to_dict(self) -> dict[str, Any]:
        """Serializes the Result and all nested scores to a JSON-compatible dictionary."""
        return {
            "id": self.id,
            "run_id": self.run_id,
            "scenario_id": self.scenario_id,
            "created_at": self.created_at,
            "overall_passed": self.overall_passed,
            "scores": [score.to_dict() for score in self.scores],
            "metrics": copy.deepcopy(self.metrics),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Result":
        """Deserializes a Result and all nested scores from a dictionary.

        Note:
            'overall_passed' is a computed/read-only output field. It is ignored on input
            to preserve tamper resistance and allow round-tripping serialized results.
            All other unknown keys are rejected.
        """
        data = _require_dict(data, "Result")
        _reject_unknown_keys(
            data,
            {"id", "run_id", "scenario_id", "created_at", "scores", "metrics"},
            "Result",
            ignored={"overall_passed"},
        )
        scores_data = data.get("scores", [])
        metrics = data.get("metrics", {})
        if not isinstance(scores_data, list):
            raise ValueError(f"Result.scores must be a list, got {type(scores_data).__name__}")
        if not isinstance(metrics, dict):
            raise ValueError(f"Result.metrics must be a dictionary, got {type(metrics).__name__}")
        validate_json_compatible(metrics, "Result.metrics")
        try:
            return cls(
                id=_require_field(data, "id", "Result"),
                run_id=_require_field(data, "run_id", "Result"),
                scenario_id=_require_field(data, "scenario_id", "Result"),
                created_at=_require_field(data, "created_at", "Result"),
                scores=[Score.from_dict(score_dict) for score_dict in scores_data],
                metrics=copy.deepcopy(metrics),
            )
        except KeyError as exc:
            raise ValueError(f"Result is missing required field {exc!s}") from exc
