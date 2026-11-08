# TOOLS_LOG.md: Tooling & Collaboration Log

This log documents observed tool/collaboration usage for AgentLab **based only on available evidence** in repository artifacts and the current working state. It avoids speculation about unrecorded interactions.

**Scope:** M1/M2 committed+pushed; M3 + approved audit remediations implemented/verified (159 tests passing) and committed/pushed as `009f5c5`
**Last updated:** 2026-11-09 (final M3 verification)

## Evidence sources used
- Repository files: `CLAUDE.md`, `README.md`, `ARCHITECTURE.md`, `PROJECT_PLAN.md`, `TASKS.md`, `DECISIONS.md`, `TOOLS_LOG.md`, source/tests under `src/agentlab/` and `tests/`.
- Git history (as observed in session): `0472d26` initial commit; `9bc510f Complete M1: Core Models and Configuration`; `0d83e1baa0bf8442e1604dc60cf1e4c03c3f4ed9` / `0d83e1b` (`Complete M2: Basic Runner and Task Completion Evaluation`) pushed to `origin/main` (`9bc510f..0d83e1b`) with explicit approval (2026-11-07).
- Working tree state (current): M3 + audit-remediation changes present; `src/agentlab/agentlab.lnk`, `agent.py`, `test.py` remain untracked/out of scope for this phase.
- Test execution (2026-11-07, M2 close): `python -X dev -W error -m unittest discover -s tests` → **121 tests OK**.
- Test execution (2026-11-08, M3 verification): `python -X dev -W error -m unittest discover -s tests` → **145 tests OK**.
- Test execution (2026-11-08, post-audit remediation / Phase 5): `python -X dev -W error -m unittest discover -s tests` → **156 tests OK**.

## Tool entries

### ChatGPT
- **Role (evidenced/limited):** Not directly evidenced in repository artifacts reviewed. Any contributions not recorded in repo docs/history cannot be verified here.
- **Strengths observed:** N/A (insufficient evidence in repo)
- **Limitations/risks observed:** N/A (insufficient evidence in repo)
- **Notes:** Record specific ChatGPT contributions in future with dates and artifacts/links where possible.

### Claude
- **Role (evidenced):** Referenced as the coding assistant in `CLAUDE.md` and project workflow docs; independent M1 review outcomes are documented in `TASKS.md` (code/tests approved with minor notes; documentation review returned NOT APPROVED; corrections in progress).
- **Strengths observed (evidenced):** Provided structured review feedback leading to documented doc corrections and M2 prerequisites tracking (details recorded in TASKS as provided).
- **Limitations/risks observed (evidenced):** Review process required iteration (docs not approved on first pass); specific prerequisite details must be accurately transferred into repo docs.
- **Notes:** This log does not include private conversation transcripts; it records only outcomes evidenced in repo files.

### OpenCode
- **Role (evidenced):** Inspected repo/docs; performed M1 git closure operations only when explicitly approved by user; implemented approved M2 plan in working tree (core gates 1–5, agents/runner/evaluator/reporting/scenario/tests); performed final `runner.py` review fixes (removed unused `agent_id_resolve`, hardened event-recording error handling to finalize Run); updated `TASKS.md`, `DECISIONS.md`, `TOOLS_LOG.md`; ran test suite repeatedly.
- **M3 and audit-remediation work (evidenced):** Implemented approved M3 in the working tree (deterministic mock tools, `MockToolRegistry` enforcing `allowed_tools` with a `TOOL_CALL` attempt and denied `TOOL_RESULT` on disallowed attempts, `ToolUsingAgent`, saved-Run `ToolChoiceEvaluator`/`ToolArgsEvaluator`, scenarios and M3 tests); applied approved P1–P7, P8, and P9.A–C remediations with regression tests; recorded P9.D as deferred due to compatibility risk. Full-suite historical result for this phase: 156 tests OK (2026-11-08).
- **Strengths observed (evidenced):** Effective at incremental implementation, targeted edits, and local verification under constraints.
- **Limitations/risks observed (evidenced):** Must not overclaim closure or perform unapproved git ops; core contract tightening required one minimal M1 test adjustment (intent preserved, documented).
- **Notes (M2):** At the time of that M2 entry, no staging/committing/pushing had been performed for M2 changes. `src/agentlab/agentlab.lnk` was observed as untracked and left untouched (out of scope). M2 was subsequently committed/pushed as recorded in the Git history and `TASKS.md`.
- **Notes (M3):** No staging/committing/pushing performed for M3 or audit remediations. `src/agentlab/agentlab.lnk`, `agent.py`, and `test.py` remain untracked/local artifacts; `app.py`/`agent.py`/`test.py` were not modified/deleted/moved in this phase.

## Gaps / Follow-ups
- M3 implemented, audit-remediated, and committed/pushed as `009f5c5` (**159 tests OK**, 2026-11-09). Perform Git operations only if explicitly approved; exclude `src/agentlab/agentlab.lnk` and respect decisions about other untracked artifacts.
- **P9.D deferred:** evaluate `scenarios_dir` tightening separately (compatibility risk) before implementation.
- If Claude's full M1 review notes (including any D13) are provided, update `TASKS.md`/docs accordingly with verifiable citations.
- Keep this log factual and update at milestone boundaries.
