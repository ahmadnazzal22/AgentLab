# DECISIONS.md: Decision Log

This file records important project decisions that can be evidenced from repository artifacts (docs, code, commit history) at the time of writing.

**Status:** Initial log (M1 documentation/closure support).
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

## Notes / Gaps
- `ARCHITECTURE.md` references `docs/decisions/0001-python-primary-language.md`, but the `docs/` directory and that file are not present in the current repository tree (untracked/absent as observed). This log does not recreate missing historical records; it records evidenced decisions only.
- Future decisions should include explicit alternatives and dates when made.
