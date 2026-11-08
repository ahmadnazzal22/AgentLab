# AI Agent Evaluation & Trust Platform (AgentLab)

**AgentLab is an AI agent testing and evaluation platform, built to help people assess whether agents complete tasks correctly, use tools appropriately, and respect safety boundaries.**

> **Status: M1 and M2 are committed and pushed (`9bc510f`, `0d83e1b` on `origin/main`). M3 (tool selection and execution evaluation) plus approved audit remediations are implemented, verified (159 tests passing, 2026-11-09), and committed/pushed as `009f5c5`.** The current implementation includes a basic in-process runner, deterministic sample/tool-using agents, deterministic mock tools, task-completion and tool evaluators, and a plain-text report. No real MCP, sandbox isolation, subprocess/Docker execution, hard timeout interruption, persistence layer, or cost evaluation is implemented.

---

## 1. What is AgentLab?

An *AI agent* is an AI system that doesn't just answer questions. It also **takes actions**: it picks tools, calls them, reads the results, and keeps going until a task is done.

That power creates a question: **how do we know an agent is good and safe enough to trust?**

AgentLab is meant to answer it. The long-term goal is to put an agent in a **controlled test environment** (a sandbox), give it a set of scenarios, watch everything it does, and score the result. The current prototype implements smaller local, in-process flows with deterministic agents and deterministic mock tools; sandboxing, real MCP, subprocess isolation, and most trust and safety checks are still planned.

Think of it as a **driving test for AI agents**: a closed course, a checklist, an examiner taking notes, and a final report.

## 2. What AgentLab evaluates (current and planned)

| # | Area | The question we answer | Status |
|---|------|------------------------|--------|
| 1 | Task completion and accuracy | Did the agent actually do the job, correctly? | `[IMPLEMENTED, basic]` |
| 2 | Tool selection and execution | Did it pick the right tools and use them properly? | `[IMPLEMENTED, basic / M3 completed, committed, and pushed]` |
| 3 | MCP integration and tool permissions | Did it stay within the permissions it was given? | `[PLANNED]` |
| 4 | Prompt injection resistance | Can hidden instructions in data trick it? | `[PLANNED]` |
| 5 | Reliability and error handling | What happens when tools fail or inputs are odd? | `[PLANNED]` |
| 6 | Performance, latency, and cost | How fast and how expensive is it? | `[PLANNED]` |
| 7 | Human approval and safety controls | Does it stop and ask before risky actions? | `[PLANNED]` |

*MCP = Model Context Protocol, a standard way for AI systems to connect to tools and data. The `docs/` directory referenced by earlier drafts is not present in this repository tree; terminology and decisions are documented in existing top-level files (`README.md`, `ARCHITECTURE.md`, `DECISIONS.md`, `TASKS.md`).*

## 3. Status labels used in this project

We are strict about honesty. Every feature is labelled:

- `[IMPLEMENTED]`: exists in the code and has been tested.
- `[IN PROGRESS]`: being built right now.
- `[PLANNED]`: an idea or design only. **It does not exist yet.**

## 4. Current status

| Item | Status |
|------|--------|
| Folder structure | `[IMPLEMENTED]` |
| Project documentation (README, CLAUDE, PROJECT_PLAN, ARCHITECTURE, TASKS, DECISIONS, TOOLS_LOG) | `[IMPLEMENTED]` (kept aligned with actual implementation) |
| Git repository (M1/M2 committed and pushed to `origin/main`) | `[IMPLEMENTED]` |
| Core data models (`Scenario`, `Event`, `Run`, `Score`, `Result`) and config (`Config`, `load_config`) | `[IMPLEMENTED]` |
| Basic in-process runner (batch agent contract, post-execution checks only) | `[IMPLEMENTED]` |
| Deterministic `SampleAgent` and `ToolUsingAgent` | `[IMPLEMENTED]` |
| Task-completion evaluation and plain-text report | `[IMPLEMENTED]` |
| Deterministic mock tool framework + `MockToolRegistry` | `[IMPLEMENTED, M3 completed, committed, and pushed]` |
| Tool choice / tool argument evaluators (saved `Run` only) | `[IMPLEMENTED, M3 completed, committed, and pushed]` |
| Audit remediations (P1–P7, P9.A–C) with regression tests | `[IMPLEMENTED, M3 completed, committed, and pushed; 159 tests passing]` |
| Real MCP, sandbox isolation, subprocess/Docker execution, hard timeout interruption, persistence, cost evaluation | `[PLANNED / NOT IMPLEMENTED]` |

## 5. How it works (current implementation)

**M2-style task-completion flow:**
```
Scenario  ->  BasicRunner  ->  SampleAgent  ->  TaskCompletionEvaluator  ->  Text Report
            (in-process)     (scripted)      (saved Run only)
```

**M3-style tool-use flow (committed as `009f5c5`):**
```
Scenario (allowed_tools, tool_call metadata)
    -> BasicRunner (in-process, batch)
    -> ToolUsingAgent
    -> MockToolRegistry (deterministic, deny-by-default allowlist enforcement)
    -> TOOL_CALL/TOOL_RESULT events in saved Run
    -> ToolChoiceEvaluator / ToolArgsEvaluator (saved Run only, COMPLETED required)
    -> Text Report (includes evidence_event_ids)
```

Important boundaries (actual behavior):
- `Agent.execute(scenario) -> list[Event]` (batch); agents return events and must not mutate `Run`.
- `BasicRunner` performs **post-execution only** checks for `max_steps` and `timeout_seconds`. It does **not** provide immediate interruption, hard timeout termination, subprocess isolation, Docker/sandboxing, or real MCP.
- Evaluators judge **saved `Run` records only** and do not re-run agents.
- `MockToolRegistry` enforces `Scenario.allowed_tools` before execution. Disallowed attempts record `TOOL_CALL`, do **not** execute the tool, and record a denied `TOOL_RESULT` (`status="denied"`, `reason="tool_not_allowed"`). If `allowed_tools` is missing (`None`), dispatch denies execution by default (no tool execution).
- `SampleAgent`'s tool-call/result events are a **scripted/simulated trace** (`trace_kind="scripted_demo"`, `registry_dispatched=False`), not actual mock-registry execution.
- `TaskCompletionEvaluator` requires completion evidence in result-bearing contexts; expected text appearing only as task restatement/start context does not by itself prove completion.

Full design details are in [ARCHITECTURE.md](ARCHITECTURE.md).

## 6. Project structure (current + intended)

```
agentlab/
├── README.md             Project overview.
├── app.py                Local sample/demo script (M2-style task-completion flow). Root artifact; unmodified in audit remediation phase.
├── agent.py              Local root-level experiment/script artifact (untracked). Not part of the core package; not modified/deleted/moved.
├── test.py               Local root-level experiment/script artifact (untracked). Not part of the core package; not modified/deleted/moved.
├── CLAUDE.md             Working rules/context for Claude Code.
├── PROJECT_PLAN.md       Roadmap.
├── ARCHITECTURE.md       System design (implemented + planned).
├── TASKS.md              Milestones/checklists.
├── DECISIONS.md          Decision log (factual/evidenced).
├── TOOLS_LOG.md          Tool/collaboration log (factual).
├── .gitignore
│
├── src/agentlab/
│   ├── agents/           Agent interface, `SampleAgent`, `ToolUsingAgent` `[IMPLEMENTED]`
│   ├── core/             Models, config, validation `[IMPLEMENTED]`
│   ├── runner/           `BasicRunner` `[IMPLEMENTED]`
│   ├── sandbox/          `[PLANNED]`
│   ├── tools/            Deterministic mock tools + registry `[IMPLEMENTED, M3 completed, committed, and pushed]`
│   ├── mcp/              `[PLANNED]`
│   ├── evaluators/       Task completion + tool choice/args `[IMPLEMENTED]` (M3 completed, committed, and pushed)
│   ├── safety/           `[PLANNED]`
│   ├── metrics/          `[PLANNED]`
│   └── reporting/        Plain-text report `[IMPLEMENTED]`
│
├── scenarios/
│   ├── task_completion/  `[IMPLEMENTED]`
│   ├── tool_use/         `[IMPLEMENTED, M3 completed, committed, and pushed]`
│   ├── prompt_injection/ `[PLANNED directory, may be empty]`
│   ├── reliability/      `[PLANNED directory, may be empty]`
│   └── safety_approval/  `[PLANNED directory, may be empty]`
│
├── tests/                Automated tests (`unittest`)
└── scripts/              Helper scripts (if present)
```

Notes:
- `docs/` (glossary/learning log/decisions subdirectory referenced by older drafts) is **not present** in this repository tree; broken links to it have been removed/fixed in this alignment pass rather than creating a new docs system.
- `runs/` persistence is a planned direction (JSON files, Git-excluded); a full persistence implementation is not part of the current closed milestones.

## 7. Getting started

Requirements: **Python 3.11+** (tested in a Python 3.12 environment). No third-party dependencies.

Run the M2-style sample flow from the repository root:

```powershell
python app.py
```

`app.py` loads the `hello_world` scenario, runs the deterministic `SampleAgent`, evaluates the saved run, and prints a text report. It does not call an external AI service, persist run records, or run the agent in a sandbox.

Run tests:

```powershell
python -X dev -W error -m unittest discover -s tests
```

To understand the project:
1. Read this README, then [PROJECT_PLAN.md](PROJECT_PLAN.md) and [ARCHITECTURE.md](ARCHITECTURE.md).
2. Check [TASKS.md](TASKS.md) and [DECISIONS.md](DECISIONS.md) for current status and rationale.
3. Treat `agent.py` and `test.py` at the repository root as local experiment/demo artifacts, not core package entry points. They are intentionally not modified in the audit-remediation phase.

## 8. Security and privacy (current state)

AgentLab is designed to evaluate AI agents and may eventually handle sensitive data. Current flows use synthetic/local test data and deterministic mock behavior:

- **No real MCP, sandbox, subprocess/Docker isolation, or hard timeout interruption** is implemented. The runner is in-process and performs post-execution checks only.
- **Mock tools are deterministic and local** (stdlib only; no network/files/real commands). Tool allowlists are enforced before execution by `MockToolRegistry`; missing allowlists deny execution by default.
- **No real secrets** (API keys, passwords) should be stored in the repository. `Config.to_dict()` excludes `api_key` and it is hidden from `repr`, but this is not complete protection (e.g., `dataclasses.asdict()` and `pickle` can still expose fields). The config loader performs best-effort key-name scanning for secrets in JSON files; it does not detect all possible secret formats.
- Test data should remain **synthetic** (fake), never real personal data.
- Risky-action approval gates, sandbox enforcement, full redaction, and production-grade isolation are **planned**, not implemented.

Security/privacy details previously referenced in `docs/security-and-privacy.md` are not present as a separate file in this repository tree; the practical constraints above reflect the current implementation.

## 9. Learning journey

This project is built **incrementally** as courses from Anthropic Claude Academy are completed. Completed so far:

| Course | Status |
|--------|--------|
| Claude Code 101 | Completed |
| AI Capabilities and Limitations | Completed |
| AI Fluency: Framework and Foundations | Completed |

Course-to-milestone connections are tracked in [TASKS.md](TASKS.md). The separate `docs/learning-log.md` file referenced by older drafts is not present in this repository tree.

## 10. Documentation map

| File | Read it when you want to... |
|------|-----------------------------|
| [README.md](README.md) | Understand what AgentLab is and its current state |
| [PROJECT_PLAN.md](PROJECT_PLAN.md) | See the long-term roadmap |
| [ARCHITECTURE.md](ARCHITECTURE.md) | See implemented and planned system design |
| [TASKS.md](TASKS.md) | See milestone status and next work |
| [DECISIONS.md](DECISIONS.md) | See evidenced project decisions |
| [TOOLS_LOG.md](TOOLS_LOG.md) | See factual tool/collaboration notes |
| [CLAUDE.md](CLAUDE.md) | See working rules for Claude Code |
