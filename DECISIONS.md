# DECISIONS.md: Decision Log

This file records important project decisions that can be evidenced from repository artifacts (docs, code, commit history) at the time of writing.

**Status:** Active log (M1 committed/pushed as `9bc510f`; M2 committed/pushed as `0d83e1b` with explicit approval; M3 implemented/verified and committed/pushed as `009f5c5` to `origin/main`).
**Last updated:** 2026-11-09

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

## 0010 — M3 Tool Selection and Execution Evaluation (implemented in working tree)
- **Decision:** Implement M3 under the unchanged batch Agent contract (`execute(scenario) -> list[Event]`) and unchanged `BasicRunner`/post-execution `max_steps` behavior. Add deterministic, stdlib-only mock tools (`src/agentlab/tools/`) and `ToolUsingAgent` driven by `Scenario.metadata.tool_call`. Enforce `Scenario.allowed_tools` in `MockToolRegistry.dispatch` **before** execution: record `TOOL_CALL` attempt, do **not** execute disallowed tool, then record `TOOL_RESULT` with `content.status="denied"`, `reason="tool_not_allowed"`, `tool`, `call_id`, and `allowed_tools`. Add `ToolChoiceEvaluator` and `ToolArgsEvaluator` that evaluate **saved `Run` records only** (no rerun), require `RunStatus.COMPLETED`, and provide `evidence_event_ids`. Scenarios: success (`tool_use/calculator_success.json`, allowed tool + correct args) and failure (`tool_use/disallowed_tool_failure.json`, disallowed attempt denied/not executed).
- **Alternatives considered/rejected:** Changing Agent/Runner to interactive tool loop (rejected: out of scope; breaks M2 contract). Executing then filtering disallowed tools (rejected: unsafe/wrong; violates explicit decision). Allowing evaluators to run on non-COMPLETED runs by default (rejected for consistency with M2; explicit COMPLETED requirement adopted). Real MCP/subprocess/Docker/network/file tools (rejected: out of M3 scope).
- **Rationale:** Delivers tool-selection/argument evaluation with auditable evidence while preserving M1/M2 architecture and safety constraints.
- **Date:** 2026-11-08 (implemented; 145 tests passing in working tree).
- **Evidence:** `src/agentlab/tools/*.py`, `src/agentlab/agents/tool_using_agent.py`, `src/agentlab/evaluators/tool_choice.py`, `src/agentlab/evaluators/tool_args.py`, `scenarios/tool_use/*.json`, `tests/test_tools.py`, `tests/test_tool_using_agent.py`, `tests/test_tool_evaluators.py`, `tests/test_m3_integration.py`.

## 0011 — Audit remediations (M3 working tree, approved scope)
- **Decision (implemented, 2026-11-08):** Apply approved audit remediations without expanding M3 scope and without Git operations.
  - **P1 (`ToolArgsEvaluator`):** fail if `expected_tool` is specified but not found in `TOOL_CALL` evidence; never compare args from a different tool. Regression: wrong tool with exact expected args must fail.
  - **P2 (`BasicRunner`):** safely handle invalid Agent returns (`None`, int, dict/non-list, etc.); normalize/record as execution failure and finalize a `FAILED` `Run` (no crash), with `agent_events_returned` counted safely.
  - **P3 (`BasicRunner`):** deterministic, bounded system event IDs (`sys-<kind>-<sha256 prefix>`) preserve identifier policy/`MAX_IDENTIFIER_LENGTH` for long valid run IDs (e.g., 64 chars). Store `run_id` in system event content for traceability.
  - **P4 (`BasicRunner`):** preserve all detected violations; record `timed_out`/`max_steps_exceeded`; status precedence: agent/execution/recording error -> `FAILED`; timeout -> `TIMEOUT`; max_steps only -> `FAILED`. Do **not** claim hard timeout interruption (post-execution checks only).
  - **P5 (`MockToolRegistry`):** deny-by-default when `allowed_tools=None` (missing allowlist): record `TOOL_CALL`, do **not** execute, record denied `TOOL_RESULT` (`tool_not_allowed`, `allowed_tools=[]`, `allowlist_missing=True`). Existing supported flow remains compatible (`ToolUsingAgent` passes explicit allowlist).
  - **P6 (`TaskCompletionEvaluator`):** conservative completion-evidence rule; expected text only in task restatement/start context (e.g., `Starting task: ...`, no final/result markers) does not prove completion. Completion evidence counted in result-bearing contexts (`TOOL_RESULT` content; `AGENT_MESSAGE` with `final`/output/result markers as implemented).
  - **P7 (`SampleAgent`):** label tool `TOOL_CALL`/`TOOL_RESULT` events as scripted/simulated trace (`trace_kind="scripted_demo"`, `registry_dispatched=False`), not mock-registry-dispatched execution.
  - **P8 (docs):** align `README/CLAUDE/PROJECT_PLAN/ARCHITECTURE/TASKS` to actual implementation; fix/remove broken `docs/*` links without creating a docs system; document `app.py`/`agent.py`/`test.py` status accurately (no delete/move/modify).
  - **P9.A:** include `evidence_event_ids` for each `Result` score in plain-text reports.
  - **P9.B:** stricter `call_id` binding in `ToolChoiceEvaluator` when `call_id` is present.
  - **P9.C:** reject duplicate tool registration in `MockToolRegistry`.
  - **P9.D (deferred, not implemented):** `scenarios_dir` tightening — separate approval required due to compatibility risk.
- **Alternatives considered/rejected:** Cross-tool arg fallback in `ToolArgsEvaluator` (rejected: can produce false pass). Crashing on bad agent return (rejected). Silent truncation of long run IDs in event IDs (rejected: ambiguity/collision risk; bounded hash chosen). Executing tools when allowlist missing (rejected). Complex new evidence ontology for task completion (rejected; conservative rule chosen).
- **Rationale:** Fix confirmed audit risks/false positives, improve safety/traceability, and keep claims honest without rewriting M1/M2 or expanding scope.
- **Date:** 2026-11-08.
- **Evidence:** `runner.py`, `evaluators/{tool_args,tool_choice,task_completion}.py`, `tools/registry.py`, `agents/sample_agent.py`, `reporting/text_report.py`, updated tests (`test_runner.py`, `test_tool_evaluators.py`, `test_tools.py`, `test_task_completion_evaluator.py`), aligned docs. Full suite: **156 tests OK** (`python -X dev -W error -m unittest discover -s tests`).

## Notes / Gaps
- The old `docs/decisions/0001-python-primary-language.md` file referenced by earlier drafts is not present in this repository tree. `DECISIONS.md` is the current in-repo decision log.
- M2 was committed/pushed to `origin/main` as `0d83e1b` (`Complete M2: Basic Runner and Task Completion Evaluation`) with explicit approval (2026-11-07). M3 + audit remediations are implemented/verified (**159 tests passing, 2026-11-09**) and committed/pushed as `009f5c5`. The 156-test result above is the historical verification recorded for the 2026-11-08 remediation. `src/agentlab/agentlab.lnk` remains untracked/out of scope. Root artifacts `agent.py`/`test.py`/`app.py` were not modified/deleted/moved in this phase.
- **P9.D deferred:** `scenarios_dir` validation tightening not approved/implemented; requires separate compatibility review.
- Future decisions should include explicit alternatives and dates when made.
