# DECISIONS.md: Decision Log

This file records important project decisions that can be evidenced from repository artifacts (docs, code, commit history) at the time of writing.

**Status:** Active log (M1 committed/pushed; M2 implemented/verified and closed in working tree; Git operations pending explicit approval).
**Last updated:** 2026-11-07

## Format
- **Decision:** What was decided
- **Alternatives considered/rejected:** Only if evidenced; otherwise noted as not recorded
- **Rationale:** Why (as evidenced)
- **Date:** Best-evidenced date or "recorded" date
- **Evidence:** Where this is documented

---

## 0001 — Primary implementation language: Python (3.11+ minimum, tested in 3.12)
- **Decision:** Use Python as the primary language. Documentation states 3.11+ minimum (tested in 3.12 environment) due to language features used.
- **Alternatives considered/rejected:** Not recorded in repository artifacts reviewed.
- **Rationale:** Consistent with project docs and implementation (standard library focus; `StrEnum`/modern typing usage implies 3.11+).
- **Date:** Recorded 2026-11-07 (decision referenced earlier in docs; original decision record path referenced as `docs/decisions/0001-python-primary-language.md` but not present in current tree).
- **Evidence:** `README.md`, `CLAUDE.md`, `ARCHITECTURE.md`, `PROJECT_PLAN.md`, `src/agentlab/core/models.py`

## 0002 — Standard library first / no third-party dependencies (initial)
- **Decision:** Prefer Python standard library; no third-party dependencies added for M1.
- **Alternatives considered/rejected:** Not recorded.
- **Rationale:** Minimize complexity and dependency risk; aligns with project principles.
- **Date:** Evidenced in M0/M1 docs (recorded 2026-11-07).
- **Evidence:** `README.md`, `CLAUDE.md`, `PROJECT_PLAN.md`, `ARCHITECTURE.md`

## 0003 — Scenario/config/result formats: JSON
- **Decision:** Use JSON for scenario definitions, configuration files, and run/result data structures (where applicable).
- **Alternatives considered/rejected:** Not recorded.
- **Rationale:** Native stdlib support, zero dependencies, structured validation.
- **Date:** Recorded in `TASKS.md`/`ARCHITECTURE.md` (M1 planning decisions).
- **Evidence:** `TASKS.md` (M1), `ARCHITECTURE.md` (Technology choices / resolved decisions)

## 0004 — Test framework: `unittest`
- **Decision:** Use Python built-in `unittest`.
- **Alternatives considered/rejected:** Not recorded.
- **Rationale:** Zero dependencies; matches stdlib-first principle.
- **Date:** Recorded in M1 decisions.
- **Evidence:** `TASKS.md`, `ARCHITECTURE.md`

## 0005 — Configuration: JSON file with safe defaults; secrets via environment variables
- **Decision:** Load configuration from JSON (e.g., `agentlab.json`) with defaults in code; read `api_key` only from `AGENTLAB_API_KEY` (env). Reject secrets in config files via best-effort key-name scanning.
- **Alternatives considered/rejected:** Not recorded.
- **Rationale:** Security and simplicity; avoid committing secrets.
- **Date:** Recorded in M1 decisions; implemented in M1.
- **Evidence:** `src/agentlab/core/config.py`, `ARCHITECTURE.md`, `TASKS.md`

## 0006 — Agent integration interface (planned/decided direction): subprocess via JSON over stdin/stdout
- **Decision (documented direction):** Use subprocess communication via JSON over stdin/stdout; sandbox responsible for security boundaries.
- **Alternatives considered/rejected:** Not recorded.
- **Rationale:** Process/memory isolation benefits vs in-process execution; security enforced by sandbox layer (planned).
- **Date:** Recorded in M1 decisions.
- **Evidence:** `TASKS.md`, `ARCHITECTURE.md`, `PROJECT_PLAN.md` (note: runner/sandbox not implemented in M1)

## 0007 — Run records storage (planned direction): local `runs/` as JSON, Git-excluded
- **Decision (documented direction):** Store run records as JSON files in local `runs/` directory excluded from Git; synthetic data only; manual deletion initially; redaction planned.
- **Alternatives considered/rejected:** Not recorded.
- **Rationale:** Privacy/safety and simplicity; Git exclusion prevents repo exposure (not encryption).
- **Date:** Recorded in M1 decisions.
- **Evidence:** `TASKS.md`, `ARCHITECTURE.md`, `.gitignore`

## 0008 — M2 Basic Runner contract and boundaries (implemented in working tree)
- **Decision:** Agent interface is `execute(scenario: Scenario) -> list[Event]`. Agents return events only and must not mutate `Run`. `BasicRunner` owns `Run` lifecycle, captures scenario snapshot, records events via `run.add_event()`, and performs **post-execution only** checks for `max_steps`/`timeout_seconds` (batch events; no immediate interruption/hard timeout/process isolation claimed). `TaskCompletionEvaluator` evaluates saved `Run` only (no rerun), requires `COMPLETED` plus evidence matching `metadata.expected_output` from explicit scenario or `run.scenario_snapshot` (no hardcoding). Simple text report renders Run + Score/Result.
- **Alternatives considered/rejected:** Letting agent mutate `Run` (rejected: violates separation). Hardcoding expected output in evaluator (rejected). Subprocess/Docker/LLM/MCP/dashboard (rejected: out of M2 scope).
- **Rationale:** Matches approved M2 scope and ARCHITECTURE separation (Runner vs Evaluator).
- **Date:** 2026-11-07 (implemented; 121 tests passing in working tree).
- **Evidence:** `src/agentlab/agents/base.py`, `sample_agent.py`, `src/agentlab/runner/runner.py`, `src/agentlab/evaluators/task_completion.py`, `src/agentlab/reporting/text_report.py`, `scenarios/task_completion/hello_world.json`, M2 tests.

## 0009 — M2 Sample Agent location and core gate handling details
- **Decision:** Reusable Sample Agent implemented in `src/agentlab/agents/` (no `examples/` wrapper in M2) for importability/testing. M1 review gates (1–5) implemented in `core` with tests. `Result.from_dict` explicitly ignores computed `overall_passed` input (tamper-resistant/round-trip) while rejecting other unknown keys. Case-insensitive duplicate prevention is supported via `normalize_identifier_for_comparison()`; full enforcement deferred to a central storage/registry layer when implemented. `runs_dir` write-time containment is provided as `resolve_path_within_storage()` (`resolve()`+`is_relative_to()`).
- **Alternatives considered/rejected:** `examples/`-only agent (rejected for M2 testability). Rejecting `overall_passed` in `Result.from_dict` (rejected: breaks self-serialization/tamper-resistance test contract).
- **Rationale:** Minimal, testable M2 delivery within scope; preserves M1 security intent; documents bounded exceptions.
- **Date:** 2026-11-07.
- **Evidence:** `src/agentlab/core/models.py`, `src/agentlab/core/config.py`, `tests/test_m2_prerequisites.py`, `tests/test_config.py` (minimal intent-preserving update), `TASKS.md`.

## Notes / Gaps
- `ARCHITECTURE.md` references `docs/decisions/0001-python-primary-language.md`, but the `docs/` directory and that file are not present in the current repository tree (untracked/absent as observed). This log does not recreate missing historical records; it records evidenced decisions only.
- M2 changes are in the working tree and not yet committed/pushed (no git operations performed). M2 closed by user confirmation (2026-11-07); Git operations pending explicit approval. `src/agentlab/agentlab.lnk` is untracked/out of scope.
- Future decisions should include explicit alternatives and dates when made.
