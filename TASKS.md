# TASKS.md: Development Milestones

This is the **living to-do list** of AgentLab. It changes as the project grows and as you complete new courses.

**Last updated:** 2026-11-03

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

**All five architectural decisions for M1 have been approved and documented.**
Before starting M1 code implementation:
1. Complete remaining M0 owner actions (Git identity configuration and first commit).
2. Wait for explicit approval to begin M1 code implementation.

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
- [x] Initialize Git on `main` (**no commits yet**)
- [ ] Configure your Git identity (`user.name`, `user.email`) *(owner action)*
- [ ] Make the first commit *(after identity is configured, with your approval)*

### M1: Core models and configuration `[PLANNED]`
- [x] Decide scenario and result file format (JSON chosen)
- [x] Decide how agents plug in (Subprocess via JSON stdin/stdout chosen; Sandbox enforces security)
- [x] Decide configuration format (JSON with safe defaults in code chosen)
- [x] Choose test approach (Python built-in unittest framework chosen)
- [x] Decide run records storage and retention (local runs/ as JSON, Git-excluded, manual deletion, synthetic data, redaction)
- [ ] Define Scenario, Run, Event, Result, Score shapes in `core/`
- [ ] Basic configuration handling implementation
- [ ] Add first tests in `tests/`
- **Course unlock:** TBD

### M2: Basic runner and task-completion evaluation `[PLANNED]`
- [ ] Minimal runner in `runner/`
- [ ] One simple sample agent in `examples/`
- [ ] First scenario in `scenarios/task_completion/`
- [ ] First evaluator (task completion) in `evaluators/`
- [ ] First plain-text report in `reporting/`
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
