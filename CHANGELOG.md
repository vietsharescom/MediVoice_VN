# CHANGELOG -- MediVoice VN
# ISO/IEC 42001:2023 Clause 10.2
# Forked from: MediVoice AI (Canada) v2.61.3

## [v0.2.0] -- 2026-06-03 -- refactor: lean documentation system
- refactor: replace 9-type report system with 4-file tracking (CLAUDE + BACKLOG + DECISIONS + CHANGELOG)
- refactor: CLAUDE.md v1.1 — merge session state, FID threshold 100 LOC, lean rules
- feat: BACKLOG.md — simple kanban (WAITING/TODO/DOING/DONE/DEFERRED)
- feat: DECISIONS.md — ADR lightweight (replaces 20+ ISO clause docs)
- chore: remove LATEST_SESSION.md + TASK_BACKLOG.md (merged/replaced)
- lesson: CA had 126 docs for 1 dev — VN starts lean, adds docs when value is clear

## [v0.1.0] -- 2026-06-03 -- docs: project kickoff documentation

- docs: CLAUDE.md v1.0 — VN-specific rules, ISO_VN framework, legal constraints
- docs: PROJECT_KICKOFF.md — S1-S9 complete (S10 pending Andy approval)
- docs: BRS.md v1.0 — business requirements for VN market
- docs: VISION.md v1.0 — product vision, flows, architecture, roadmap
- docs: LATEST_SESSION.md — initial session record
- docs: TASK_BACKLOG.md — full task tracking initialized
- infra: project structure created at C:\Projects\MediVoice_VN
- infra: git repository initialized

**Forked base:** MediVoice AI (Canada) v2.61.3 | 643/643 PASS
**Status:** Documentation phase — no code yet. Awaiting PROJECT_KICKOFF S10 approval.
