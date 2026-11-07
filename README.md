# AgentLab

**An AI Agent Testing and Evaluation Platform.**

> **Status: M1 provisionally complete (code/tests).** Core data models and configuration are implemented in `src/agentlab/core/`. Most features remain planned. Documentation corrections are in progress following independent review.

---

## 1. What is AgentLab?

An *AI agent* is an AI system that doesn't just answer questions. It also **takes actions**: it picks tools, calls them, reads the results, and keeps going until a task is done.

That power creates a question: **how do we know an agent is good and safe enough to trust?**

AgentLab is meant to answer it. The idea is to put an agent in a **controlled test environment** (a sandbox), give it a set of scenarios, watch everything it does, and score the result.

Think of it as a **driving test for AI agents**: a closed course, a checklist, an examiner taking notes, and a final report.

## 2. What AgentLab will evaluate

| # | Area | The question we want to answer | Status |
|---|------|--------------------------------|--------|
| 1 | Task completion and accuracy | Did the agent actually do the job, correctly? | `[PLANNED]` |
| 2 | Tool selection and execution | Did it pick the right tools and use them properly? | `[PLANNED]` |
| 3 | MCP integration and tool permissions | Did it stay within the permissions it was given? | `[PLANNED]` |
| 4 | Prompt injection resistance | Can hidden instructions in data trick it? | `[PLANNED]` |
| 5 | Reliability and error handling | What happens when tools fail or inputs are odd? | `[PLANNED]` |
| 6 | Performance, latency, and cost | How fast and how expensive is it? | `[PLANNED]` |
| 7 | Human approval and safety controls | Does it stop and ask before risky actions? | `[PLANNED]` |

*MCP = Model Context Protocol, a standard way for AI systems to connect to tools and data. See [docs/GLOSSARY.md](docs/GLOSSARY.md) for plain-language definitions of every term.*

## 3. Status labels used in this project

We are strict about honesty. Every feature is labelled:

- `[IMPLEMENTED]`: exists in the code and has been tested.
- `[IN PROGRESS]`: being built right now.
- `[PLANNED]`: an idea or design only. **It does not exist yet.**

## 4. Current status

| Item | Status |
|------|--------|
| Folder structure | `[IMPLEMENTED]` |
| Project documentation (README, CLAUDE, PROJECT_PLAN, ARCHITECTURE, TASKS) | `[IMPLEMENTED]` |
| Git repository (initialized with commits, remote configured) | `[IMPLEMENTED]` |
| Core data models (`Scenario`, `Event`, `Run`, `Score`, `Result`) and config (`Config`, `load_config`) | `[IMPLEMENTED]` |
| Runner, sandbox, tools, MCP, evaluators, safety, metrics, reporting | `[PLANNED]` |

## 5. How it is intended to work (high level)

```
Scenario  ->  Runner  ->  Sandbox + Agent  ->  Evaluators  ->  Report
(the test)   (runs it)   (safe environment)   (score it)     (results)
                              |
                       Metrics (time, tokens, cost)
```

Full details are in [ARCHITECTURE.md](ARCHITECTURE.md). Core is implemented; other components are proposed/planned.

## 6. Project structure

Some folders contain their own `README.md` explaining their purpose (where created). The structure below shows the intended/planned layout; not all directories exist yet.

```
agentlab/
├── README.md             You are here. Overview of the project.
├── CLAUDE.md             Rules and context for Claude Code when working here.
├── PROJECT_PLAN.md       Long-term roadmap (the "big picture").
├── ARCHITECTURE.md       Proposed system design.
├── TASKS.md              Milestones and checklists (the "to-do list").
├── .gitignore            Tells Git which files to never track (secrets, caches).
│
├── src/agentlab/         The application code (core implemented; other modules planned).
│   ├── core/             Shared building blocks (data shapes and config) `[IMPLEMENTED]`
│   ├── runner/           Runs an agent through a scenario. `[PLANNED]`
│   ├── sandbox/          The controlled, restricted environment. `[PLANNED]`
│   ├── tools/            Fake/mock tools the agent can use during tests. `[PLANNED]`
│   ├── mcp/              MCP integration and permission checks. `[PLANNED]`
│   ├── evaluators/       The "judges" that score agent behavior. `[PLANNED]`
│   ├── safety/           Human-approval gates and safety controls. `[PLANNED]`
│   ├── metrics/          Latency, token usage, and cost tracking. `[PLANNED]`
│   └── reporting/        Turns results into readable reports. `[PLANNED]`
│
├── scenarios/            Test cases, kept as data (not code).
│   ├── task_completion/
│   ├── tool_use/
│   ├── prompt_injection/
│   ├── reliability/
│   └── safety_approval/
│
├── tests/                Automated tests for AgentLab itself.
├── docs/                 Extra documentation, glossary, learning log.
│   └── decisions/        Short records of "why we chose X".
├── examples/             Small sample agents to test the platform with.
└── scripts/              Helper scripts (setup, utilities).
```

## 7. Getting started

Core models and configuration can be imported from `agentlab.core`. Most functionality is not yet runnable. To look around:

1. Read this README, then [PROJECT_PLAN.md](PROJECT_PLAN.md) and [ARCHITECTURE.md](ARCHITECTURE.md).
2. Check [TASKS.md](TASKS.md) to see what is done and what is next.
3. Read [docs/GLOSSARY.md](docs/GLOSSARY.md) whenever a term is unfamiliar.

Requirements will be added here as code is written. The primary language is **Python** (minimum **3.11+**, tested in a Python 3.12 environment; uses `StrEnum` and modern type syntax). No third-party dependencies have been added.

## 8. Security and privacy, from day one

AgentLab runs AI agents and may handle sensitive data, so safety is part of the design, not an afterthought:

- Test agents are **planned** to run in a sandbox with the least access they need.
- **No real secrets** (API keys, passwords) are ever stored in the repository. `Config.to_dict()` excludes `api_key` and it is hidden from `repr`, but this is not complete protection (e.g., `dataclasses.asdict()` and `pickle` can still expose fields). The config loader performs best-effort key-name scanning for secrets in JSON files; it does not detect all possible secret formats.
- Test data must be **synthetic** (fake), never real personal data.
- Risky actions are **planned** to require human approval by design.
- **Redaction** of sensitive values in logs/reports is **planned**, not implemented.

Details: [docs/security-and-privacy.md](docs/security-and-privacy.md).

## 9. Learning journey

This project is built **incrementally** as courses from Anthropic Claude Academy are completed. Completed so far:

| Course | Status |
|--------|--------|
| Claude Code 101 | Completed |
| AI Capabilities and Limitations | Completed |
| AI Fluency: Framework and Foundations | Completed |

How each course informs the project is tracked in [docs/learning-log.md](docs/learning-log.md) and [TASKS.md](TASKS.md).

## 10. Documentation map

| File | Read it when you want to... |
|------|-----------------------------|
| [README.md](README.md) | Understand what AgentLab is |
| [PROJECT_PLAN.md](PROJECT_PLAN.md) | See the long-term roadmap |
| [ARCHITECTURE.md](ARCHITECTURE.md) | See how the system works (implemented and planned) |
| [TASKS.md](TASKS.md) | See what to work on next |
| [CLAUDE.md](CLAUDE.md) | See the rules Claude Code follows here |
| [docs/security-and-privacy.md](docs/security-and-privacy.md) | Understand safety rules |
| [docs/GLOSSARY.md](docs/GLOSSARY.md) | Look up a term |
| [docs/learning-log.md](docs/learning-log.md) | Track what was learned and applied |
