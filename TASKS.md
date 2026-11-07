# TASKS.md: Development Milestones

This is the **living to-do list** of AgentLab. It changes as the project grows and as you complete new courses.

**Last updated:** 2026-11-07

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

**M2 implemented and verified in working tree (closed; Git operations pending explicit approval):** First full flow complete — `Scenario → Sample Agent → Runner → Run Record → Task Completion Evaluator → Text Report`. M2 gates (1–5) implemented in `core`. Full suite: **121 tests passing** (`python -X dev -W error -m unittest discover -s tests`, 2026-11-07). No stage/commit/push performed. Untracked `src/agentlab/agentlab.lnk` excluded from scope.

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
- [x] Write `docs/security-and-privacy.md`, `docs/GLOSSARY.md`, `docs/learning-log.md`
- [x] Record first decision (Python as primary language)
- [x] Add `.gitignore`
- [x] Initialize Git on `main`
- [x] Configure your Git identity (`user.name`, `user.email`)
- [x] Make the first commit (`0472d26`)

### M1: Core models and configuration `[IN PROGRESS]`
- [x] Decide scenario and result file format (JSON chosen)
- [x] Decide how agents plug in (Subprocess via JSON stdin/stdout chosen; Sandbox enforces security)
- [x] Decide configuration format (JSON with safe defaults in code chosen)
- [x] Choose test approach (Python built-in unittest framework chosen)
- [x] Decide run records storage and retention (local runs/ as JSON, Git-excluded, manual deletion, synthetic data, redaction)
- [x] Define Scenario, Run, Event, Result, Score shapes in `core/`
- [x] Basic configuration handling implementation
- [x] Add first tests in `tests/`
- **Course unlock:** TBD

### M2: Basic runner and task-completion evaluation `[IMPLEMENTED]` *(verified in working tree, 121 tests OK; Git operations pending explicit approval)*
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
- **Course unlock:** TBD

### M3: Tool selection and execution `[PLANNED]`
- [ ] Mock tool framework in `tools/`
- [ ] Record every tool call as an Event
- [ ] Scenarios in `scenarios/tool_use/`
- [ ] Evaluators for tool choice and tool arguments
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
- [ ] Add a decision record for every new dependency or major choice
- [ ] Re-check security and privacy rules (`docs/security-and-privacy.md`)
- [ ] Update `docs/learning-log.md`

---

## 6. How to update this file

1. **After finishing work:** tick the boxes and update the milestone status label.
2. **After completing a new course:**
   1. Add it to the *Courses completed* table.
   2. Tell Claude Code what the course covered (Claude should **not** guess).
   3. Decide together which milestones it unlocks and fill in **Course unlock**.
   4. Add or adjust tasks.
   5. Add an entry to `docs/learning-log.md`.
3. **When plans change:** edit the tasks here, then update `PROJECT_PLAN.md` if the change is big.
4. Update the **Last updated** date at the top.
