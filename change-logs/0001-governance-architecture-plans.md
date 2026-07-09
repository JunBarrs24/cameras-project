# 0001: Repo governance, architecture, and phase plans

Date: 2026-07-09
Author: Claude Code session, directed and validated by Juan Barrera

## What changed

- `ARCHITECTURE.md`: platform design (hybrid edge + cloud, pipeline, vertical profiles, event schema, retention, roadmap).
- Governance: `AGENTS.md` (rule index, kept minimal), `CLAUDE.md` (symlink to AGENTS.md), `docs/HOW_TO_WRITE_DOCUMENTS.md`, `docs/HOW_TO_COMMIT.md`, `docs/HOW_TO_VALIDATE.md`, `docs/HOW_TO_LOG_CHANGES.md`.
- `docs/DECISIONS.md`: seeded with D-001 to D-006 (validated in conversation) and D-007, D-008 (proposed, awaiting validation).
- `docs/BIOMETRICS.md`: analysis and checklist for the postponed biometrics capability.
- Phase plans: `docs/plans/PHASE_0.md` to `PHASE_3.md`.
- Change-log system: this folder, this entry.
- `src/main.py`: camera credentials removed from code before the first push (read from environment instead); `.env` gitignored, `.env.example` added.
- Repository published to `https://github.com/JunBarrs24/cameras-project.git` (origin, branch main).

## Why

Establish the rules, decisions, and detailed plans before writing platform code, so every future change (human or agent) follows the same validators, logging, and writing style, and so the design decisions have one immutable source of truth.

## Files created / modified / deleted

Created: ARCHITECTURE.md, AGENTS.md, CLAUDE.md (symlink), docs/HOW_TO_WRITE_DOCUMENTS.md, docs/HOW_TO_COMMIT.md, docs/HOW_TO_VALIDATE.md, docs/HOW_TO_LOG_CHANGES.md, docs/DECISIONS.md, docs/BIOMETRICS.md, docs/plans/PHASE_0.md, docs/plans/PHASE_1.md, docs/plans/PHASE_2.md, docs/plans/PHASE_3.md, change-logs/INDEX.md, change-logs/0001-governance-architecture-plans.md, .env.example
Modified: src/main.py (credentials to env), .gitignore (.env, data/)
Deleted: none

## Validation

Documents only, no Python behavior changed, so ruff/ty/pytest do not apply yet (tooling itself arrives in Phase 0 step 1). Manual checks: grep confirms zero em-dashes outside the rule that names the character; all AGENTS.md links resolve; `src/main.py` contains no credentials before the initial push.

## Decisions, biases, tradeoffs

Applies D-001 to D-006 (validated). Proposes D-007 (toolchain with ty) and D-008 (Telegram before WhatsApp), both awaiting validation by Juan.
