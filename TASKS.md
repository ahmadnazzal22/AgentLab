# TASKS.md: Development Milestones

This is the **living to-do list** of AgentLab. It changes as the project grows and as you complete new courses.

**Last updated:** 2026-11-09 (M3 audit remediation and final verification)

## Legend

- `[x]` done and verified
- `[ ]` not done yet
- Status labels: `[IMPLEMENTED]`, `[IN PROGRESS]`, `[PLANNED]`

---

## 1. Courses completed

| # | Course | Status | Milestones it informs |
|---|--------|--------|------------------------|
| 1 | Claude Code 101 | Completed | M0 (way of working, `CLAUDE.md`) |
| 2 | AI Capabilities and Limitations | Completed | M0 (why testing matters); later: M5 (injection), M6 (reliability) |
| 3 | AI Fluency: Framework and Foundations | Completed | M0 (human-in-the-loop mindset); later: M8 (approval and safety) |

*"Milestones it informs" is a starting suggestion. Adjust it to match what you actually learned.*

## 2. Courses planned or upcoming

| Course | Status | Milestones it may unlock |
|--------|--------|---------------------------|
| *(add the next course here)* | Not started | TBD |

---

## 3. Current focus

**M1 committed/pushed:** `9bc510f` (`Complete M1: Core Models and Configuration`) on `main`, pushed to `origin/main`. Claude M1 review: code/tests approved with minor notes; D13 not provided/verified.

**M2 committed/pushed:** `0d83e1b` (`Complete M2: Basic Runner and Task Completion Evaluation`) on `main`, pushed to `origin/main` (`9bc510f..0d83e1b`, 2026-11-07) with explicit approval. M2 flow: `Scenario → SampleAgent → BasicRunner → Run → TaskCompletionEvaluator → Text Report` (in-process, batch, post-execution checks only).

**M3 completed in the working tree (not committed or pushed):** Tool Selection and Execution Evaluation is implemented (`src/agentlab/tools/`, `ToolUsingAgent`, `ToolChoiceEvaluator`, `ToolArgsEvaluator`, `scenarios/tool_use/*`, M3 tests). Approved remediations implemented and regression-tested: **P1** `ToolArgsEvaluator` fails if a specified `expected_tool` is absent from `TOOL_CALL` events and never compares args from a different tool; **P2** `BasicRunner` safely handles invalid agent returns (`None`/int/non-list) and returns a finalized `FAILED` `Run`; **P3** deterministic bounded system event IDs preserve identifier policy/length for long run IDs (traceability via `run_id` in content); **P4** all detected violations preserved with approved status precedence and post-execution-only semantics; **P5** `MockToolRegistry` deny-by-default when `allowed_tools=None` (no execution); **P6** conservative `TaskCompletionEvaluator` completion-evidence rule (task restatement/start alone is insufficient); **P7** `SampleAgent` tool trace marked scripted/simulated (`trace_kind="scripted_demo"`, `registry_dispatched=False`); **P8** docs aligned to actual implementation and broken `docs/*` links fixed/removed without creating a docs system; **P9.A–C** `evidence_event_ids` in result text reports, stricter `call_id` binding in `ToolChoiceEvaluator` where applicable, duplicate tool registration rejected. **P9.D (`scenarios_dir` tightening) deferred** — not approved/implemented; handle separately due to compatibility risk.

**Current verification:** `python -X dev -W error -m unittest discover -s tests` → **159 tests passing** (2026-11-09, Windows). **No Git staging/commit/push/reset performed.**

**Unmodified root/local artifacts (documented only):** `app.py` (M2-style sample entry point), `agent.py` (untracked local experiment/script), `test.py` (untracked local experiment/script). `src/agentlab/agentlab.lnk` remains untracked/out of scope.

---

## 4. Milestones

### M0: Foundation `[IMPLEMENTED]`
- [x] Explore the environment (Python 3.12, Git, Node present; no Docker)
- [x] Create folder structure
- [x] Write `README.md`
- [x] Write `CLAUDE.md`
- [x] Write `PROJECT_PLAN.md`
- [x] Write `ARCHITECTURE.md`
- [x] Write `TASKS.md`
- [x] Write security/privacy, glossary, and learning-log documentation (referenced in M0; those `docs/` files are not present in the current repository tree)
- [x] Record first decision (Python as primary language)
- [x] Add `.gitignore`
- [x] Initialize Git on `main`
- [x] Configure your Git identity (`user.name`, `user.email`)
- [x] Make the first commit (`0472d26`)

### M1: Core models and configuration `[IMPLEMENTED]` *(committed/pushed as `9bc510f`)*
- [x] Decide scenario and result file format (JSON chosen)
- [x] Decide how agents plug in (Subprocess via JSON stdin/stdout chosen; Sandbox enforces security)
- [x] Decide configuration format (JSON with safe defaults in code chosen)
- [x] Choose test approach (Python built-in unittest framework chosen)
- [x] Decide run records storage and retention (local runs/ as JSON, Git-excluded, manual deletion, synthetic data, redaction)
- [x] Define Scenario, Run, Event, Result, Score shapes in `core/`
- [x] Basic configuration handling implementation
- [x] Add first tests in `tests/`
- **Course unlock:** TBD

### M2: Basic runner and task-completion evaluation `[IMPLEMENTED]` *(committed/pushed as `0d83e1b`, 2026-11-07)*
- [x] Minimal runner in `runner/` (`src/agentlab/runner/runner.py`, `BasicRunner`; post-execution `max_steps`/`timeout_seconds` checks only)
- [x] One simple deterministic sample agent (`src/agentlab/agents/sample_agent.py`; reusable implementation in `src/` for M2 testability; no `examples/` wrapper added)
- [x] First scenario in `scenarios/task_completion/` (`hello_world.json`, `metadata.expected_output`)
- [x] First evaluator (task completion) in `evaluators/` (`TaskCompletionEvaluator`; evaluates saved `Run` only, no rerun, no hardcoded expected output)
- [x] First plain-text report in `reporting/` (`render_text_report`)
- [x] M2 integration + unit tests added (`tests/test_m2_prerequisites.py`, `test_agents.py`, `test_runner.py`, `test_task_completion_evaluator.py`, `test_m2_integration.py`); full suite **121 tests OK** (2026-11-07)
- **M2 prerequisites (from Claude's M1 code review):** Addressed in `core` as M2 gates and verified by tests (limited M1 test update: `test_config.py::test_to_dict_rejects_nan_infinity` adapted to fail-fast JSON validation; intent preserved).
  - [x] **1. Identifier Policy:** Alphanumeric start, reject trailing dot, reject Windows reserved names (`CON/NUL/COM1` etc.), and case-insensitive duplicate-prevention policy support (`normalize_identifier_for_comparison`; storage-layer enforcement when a central registry exists).
  - [x] **2. Config.runs_dir Constraints:** Reject absolute/drive/leading-separator paths, `..`, and NUL. Write-time containment check available via `resolve()` + `is_relative_to()` (`resolve_path_within_storage`).
  - [x] **3. JSON Compatibility Validation:** String keys, supported JSON values, finite numbers, reject `set`/unsupported objects, depth limit.
  - [x] **4. from_dict Error Contract:** Input type validated; invalid/missing/type errors normalized to `ValueError` with clear field/problem.
  - [x] **5. Unknown-key Rejection:** `load_config` and `from_dict` reject unknown keys with clear errors (`Result.from_dict` explicitly ignores computed `overall_passed` only, to preserve tamper resistance/round-trip).
- **Git state (corrected):** committed/pushed to `origin/main` as `0d83e1b` (`Complete M2: Basic Runner and Task Completion Evaluation`) with explicit approval; `src/agentlab/agentlab.lnk` excluded.
- **Course unlock:** TBD

### M3: Tool selection and execution `[COMPLETED in working tree; not committed or pushed]` *(159 tests OK, 2026-11-09)*
- [x] Mock tool framework in `tools/` (`src/agentlab/tools/`; deterministic stdlib-only mocks, no network/files/real commands)
- [x] Record every tool call as Events: `TOOL_CALL` attempt + `TOOL_RESULT` (`status=ok|error|denied`). `Scenario.allowed_tools` enforced before execution; disallowed attempts record `TOOL_CALL`, do **not** execute tool, record denied `TOOL_RESULT` (`reason="tool_not_allowed"`). Missing allowlist (`allowed_tools=None`) denies execution by default (P5). Duplicate tool registration rejected (P9.C).
- [x] Scenarios in `scenarios/tool_use/` (`calculator_success.json`: allowed tool + correct args; `disallowed_tool_failure.json`: disallowed attempt denied/not executed)
- [x] Evaluators for tool choice and tool arguments (`ToolChoiceEvaluator`, `ToolArgsEvaluator`); evaluate saved `Run` only (no rerun), require `RunStatus.COMPLETED`, include `evidence_event_ids`. P1: if `expected_tool` is specified but absent from `TOOL_CALL` events, `ToolArgsEvaluator` fails and never compares args from a different tool. P9.B: stricter `call_id` binding where applicable.
- [x] Batch Agent contract preserved (`execute(scenario) -> list[Event]`); `BasicRunner` scope unchanged (in-process, post-execution checks only). P2/P3/P4 remediations applied (safe invalid returns, deterministic bounded system IDs, all violations preserved with approved status precedence).
- [x] `TaskCompletionEvaluator` conservative completion-evidence rule (P6): task restatement/start alone does not prove completion.
- [x] `SampleAgent` tool trace labeled scripted/simulated, not registry-dispatched (P7).
- [x] Plain-text report includes `evidence_event_ids` for `Result` scores (P9.A).
- [x] Docs aligned to actual implementation; broken `docs/*` links fixed/removed without creating a docs system (P8). `app.py`/`agent.py`/`test.py` not modified/deleted/moved.
- [x] M3 + audit regression tests added/updated; full suite **156 tests OK** (`python -X dev -W error -m unittest discover -s tests`, 2026-11-08).
- [x] **M3 closure:** implementation and audit remediations reviewed; full suite passes (159 tests). No Git staging/commit/push performed. **P9.D `scenarios_dir` tightening remains deferred** (separate approval required; compatibility risk).
- **Course unlock:** TBD

### M4: MCP integration and permissions `[PLANNED]`
- [ ] Decide what is simulated vs. real MCP (decision record)
- [ ] MCP connection layer in `mcp/`
- [ ] Permission model (allowed / denied actions per tool)
- [ ] Evaluator detecting out-of-bounds tool use
- **Course unlock:** TBD

### M5: Prompt injection resistance `[PLANNED]`
- [ ] Safe, synthetic injection scenarios in `scenarios/prompt_injection/`
- [ ] Evaluator detecting that an injected instruction was followed
- [ ] Documentation of injection categories covered and *not* covered
- **Course unlock:** TBD

### M6: Reliability and error handling `[PLANNED]`
- [ ] Fault-injecting mock tools (fail, time out, return bad data)
- [ ] Scenarios in `scenarios/reliability/`
- [ ] Repeated-run consistency checks
- [ ] Evaluators for graceful recovery
- **Course unlock:** TBD

### M7: Performance, latency, and cost `[PLANNED]`
- [ ] Timing per step and per run in `metrics/`
- [ ] Token counting and cost estimation
- [ ] Optional budget limits (time, steps, spend)
- [ ] Summary of metrics in reports
- **Course unlock:** TBD

### M8: Human approval and safety controls `[PLANNED]`
- [ ] Approval-gate mechanism in `safety/`
- [ ] Scenarios in `scenarios/safety_approval/`
- [ ] Evaluator confirming the agent paused and did not bypass the gate
- [ ] Safety limits (blocked action types)
- **Course unlock:** TBD

### M9: Reporting and optional dashboard `[PLANNED]`
- [ ] Markdown reports with evidence
- [ ] Compare results between runs
- [ ] Decide whether a dashboard is worth building (decision record)
- **Course unlock:** TBD

---

## 5. Ongoing tasks (every milestone)

- [ ] Keep status labels honest across all docs
- [ ] Add or update tests for new logic
- [ ] Update `ARCHITECTURE.md` when design changes
- [ ] Add a factual decision record for every new dependency or major choice (`DECISIONS.md`)
- [ ] Re-check security/privacy claims against actual implementation (no sandbox/MCP/hard-timeout claims unless implemented)
- [ ] Update `TOOLS_LOG.md` / course notes in `TASKS.md` as appropriate (old `docs/` learning-log/security files are not present)

---

## 6. How to update this file

1. **After finishing work:** tick the boxes and update the milestone status label.
2. **After completing a new course:**
   1. Add it to the *Courses completed* table.
   2. Tell Claude Code what the course covered (Claude should **not** guess).
   3. Decide together which milestones it unlocks and fill in **Course unlock**.
   4. Add or adjust tasks.
   5. Record factual course/milestone notes in `TASKS.md` or `DECISIONS.md` as appropriate (old `docs/learning-log.md` is not present).
3. **When plans change:** edit the tasks here, then update `PROJECT_PLAN.md` if the change is big.
4. Update the **Last updated** date at the top.
