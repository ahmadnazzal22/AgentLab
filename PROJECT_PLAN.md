# PROJECT_PLAN.md: Long-Term Roadmap

> **Status of this document:** Roadmap with implementation progress.
> Phase 0 done. Phase 1 and Phase 2 are implemented (M1/M2 committed and pushed). Phase 3 scope (tool selection/execution evaluation, mock tools, tool evaluators) is implemented and audit-remediated in the working tree (**156 tests passing, 2026-11-08**) but **not committed/closed**. Other phases remain `[PLANNED]` and may change. Current implementation is in-process and scope-limited: no real MCP, sandbox isolation, subprocess/Docker execution, hard timeout interruption, persistence layer, or cost evaluation.

---

## 1. Vision

Build a platform where anyone can take an AI agent, run it through controlled test scenarios, and get a clear, trustworthy report on **how well it works and how safe it is**.

## 2. Goals

1. Measure whether agents complete tasks correctly.
2. Check that agents choose and use tools properly.
3. Verify that agents respect MCP tool permissions.
4. Test resistance to prompt injection.
5. Test reliability and error handling.
6. Track performance, latency, and cost.
7. Verify human-approval and safety controls.
8. Produce results that are **repeatable** (same test, comparable results) and **explainable** (you can see *why* something scored the way it did).

## 3. Non-goals (for now)

- Building a production-grade hosted service.
- Building our own AI agents (we test agents; small sample agents in `examples/` are only for demonstration).
- A graphical dashboard (maybe much later, Phase 9).
- Supporting every agent framework on day one.

## 4. Guiding principles

| Principle | In plain words |
|-----------|----------------|
| Incremental | Build a little, learn, repeat. Matches your course pace. |
| Honest | Never claim a feature works before it does. |
| Modular | Each part has one job and can be replaced or improved alone. |
| Safe by default | Sandbox, least privilege, synthetic data, human approval. |
| Minimal dependencies | Standard library first. Add outside packages only with a reason. |
| Explainable | Results should show evidence, not just a score. |
| Beginner-friendly | Docs and code should be understandable to a newcomer. |

## 5. Learning foundation (completed courses)

| Course | Status | How it informs AgentLab *(to be refined by the owner)* |
|--------|--------|----------------------------------------------------------|
| Claude Code 101 | Completed | The way we work: using Claude Code, `CLAUDE.md` rules, planning before building, small reviewable steps. |
| AI Capabilities and Limitations | Completed | Why testing is needed: AI systems can be wrong, inconsistent, or manipulated, so agents must be evaluated, not assumed reliable. |
| AI Fluency: Framework and Foundations | Completed | The collaboration mindset: delegating clearly, describing tasks well, critically checking AI output (discernment), and taking responsibility (diligence). We use this for how humans review results and approve risky actions. |

*These connections are starting hypotheses. Edit them to reflect what you actually learned.*

## 6. Roadmap by phase

Each phase has a goal, what it delivers, and what must come first. Course unlocks are intentionally left **TBD**, to be filled in as you take future courses.

### Phase 0: Foundation `[IMPLEMENTED]`
- **Goal:** Create a clean, documented starting point.
- **Delivers:** Folder structure, core documentation, Git initialized, security/privacy principles written down.
- **Not included:** Any application logic.

### Phase 1: Core models and configuration `[IMPLEMENTED]` (M1, committed/pushed)
- **Goal:** Define the shared vocabulary of the system.
- **Delivered:** Data shapes for Scenario, Run, Event, Result, and Score; configuration handling with security hardening.
- **Depends on:** Phase 0.
- **Course unlock:** TBD

### Phase 2: Basic runner and task-completion evaluation `[IMPLEMENTED]` (M2, committed/pushed)
- **Goal:** Run one simple agent through one simple scenario and score whether it finished the task.
- **Delivered (scope-limited):** `BasicRunner` (in-process, batch, post-execution checks only), deterministic `SampleAgent`, `scenarios/task_completion/hello_world.json`, `TaskCompletionEvaluator` (saved `Run` only), and plain-text report.
- **Depends on:** Phase 1.
- **Course unlock:** TBD

### Phase 3: Tool selection and execution `[IMPLEMENTED in working tree, not closed]` (M3 + audit remediations)
- **Goal:** Judge *how* the agent used tools, not just the final answer.
- **Delivered (scope-limited):** Deterministic stdlib-only mock tools (`src/agentlab/tools/`), `MockToolRegistry` with allowlist enforcement before execution (deny-by-default when allowlist is missing), `ToolUsingAgent`, `TOOL_CALL`/`TOOL_RESULT` evidence (including denied/not-executed disallowed attempts), `ToolChoiceEvaluator` and `ToolArgsEvaluator` (saved `Run` only, `COMPLETED` required, `evidence_event_ids`), and `scenarios/tool_use/` success/failure cases. Audit remediations improved runner safety, evaluator correctness/binding, task-completion evidence conservatism, scripted-trace labeling, and reporting evidence.
- **Not delivered:** Real MCP, sandbox/subprocess/Docker isolation, hard timeout interruption, persistence, cost/performance evaluation.
- **Depends on:** Phase 2.
- **Course unlock:** TBD

### Phase 4: MCP integration and permissions `[PLANNED]`
- **Goal:** Test agents that use MCP servers, and verify permission boundaries are respected.
- **Delivers:** MCP connection layer, a permission model (what a tool may do), checks that detect out-of-bounds tool use.
- **Depends on:** Phase 3.
- **Course unlock:** TBD

### Phase 5: Prompt injection resistance `[PLANNED]`
- **Goal:** Check whether hostile text hidden in data can hijack the agent.
- **Delivers:** A library of safe, synthetic injection scenarios and evaluators that detect when an agent followed an injected instruction.
- **Depends on:** Phase 3 (and ideally Phase 4).
- **Course unlock:** TBD

### Phase 6: Reliability and error handling `[PLANNED]`
- **Goal:** See how agents behave when things go wrong.
- **Delivers:** Fault injection (tools that fail, time out, or return garbage), repeated-run consistency checks, evaluators for graceful recovery.
- **Depends on:** Phase 3.
- **Course unlock:** TBD

### Phase 7: Performance, latency, and cost `[PLANNED]`
- **Goal:** Measure speed and spending.
- **Delivers:** Timing, token counting, cost estimation, per-run and per-scenario summaries, optional budget limits.
- **Depends on:** Phase 2.
- **Course unlock:** TBD

### Phase 8: Human approval and safety controls `[PLANNED]`
- **Goal:** Verify agents pause for approval on risky actions, and that approval gates work.
- **Delivers:** An approval-gate mechanism, scenarios that require approval, evaluators that check the agent waited and did not bypass it.
- **Depends on:** Phases 3 and 4.
- **Course unlock:** TBD

### Phase 9: Reporting and (optional) dashboard `[PLANNED]`
- **Goal:** Make results easy to read and compare over time.
- **Delivers:** Readable reports (text/Markdown first), comparison between runs; a visual dashboard only if it is clearly worth it.
- **Depends on:** Earlier phases.
- **Course unlock:** TBD

> Phases 5 to 8 can be reordered based on which courses you complete next.

## 7. Success criteria

The project is on track when:

- A new person can read the docs and understand the project in under an hour.
- Every implemented feature has tests and is correctly labelled.
- Running the same scenario twice gives comparable, explainable results.
- No secrets or real personal data exist in the repository.
- Each of the seven evaluation areas has at least one working scenario and evaluator.

## 8. Risks and how we handle them

| Risk | Mitigation |
|------|------------|
| Scope grows too large | Strict phases; only build the current milestone. |
| Docs claim more than exists | Status labels + rule in `CLAUDE.md`. |
| Evaluating AI with AI is unreliable | Prefer rule-based checks first; treat any AI-based judging as an open question and document its limits. |
| Test content leaks sensitive data | Synthetic data only; redaction in logs. |
| Dependency bloat | Standard library first; decision record required for each new dependency. |
| Tests that actually trigger harmful actions | Sandbox plus mock tools; no real external effects. |

## 9. How this plan evolves

- After each new course, review this plan with Claude Code and update phases or priorities.
- Changes to the plan are reflected in `TASKS.md`.
- Major shifts and evidenced decisions are recorded in `DECISIONS.md`. (The old `docs/decisions/` directory is not present in this repository tree; do not create a new docs system without approval.)
