# How to log changes

Every change writes a change-log entry before it is finished. A change without a log entry is not done.

## Structure

```
change-logs/
├── INDEX.md              # global index, one line per change
├── 0001-short-slug.md    # full text of change 0001
└── 0002-short-slug.md
```

- File name: `NNNN-short-slug.md`, zero-padded sequence. The next number is the last entry in INDEX.md plus one.
- INDEX.md line format: `- 0001 (2026-07-09) [Title](0001-short-slug.md)`

## Per-change template

```markdown
# NNNN: Title

Date: YYYY-MM-DD
Author: <human or agent session>

## What changed

## Why

## Files created / modified / deleted

## Validation
Output of ruff, ty, pytest (pass/fail per tool) and any manual checks run.

## Decisions, biases, tradeoffs
Which docs/DECISIONS.md entries this change applies (e.g. "follows D-003").
If a NEW decision was needed: propose it here. It enters DECISIONS.md only
after validation by Juan or the developer.
```

## Rules

- The entry is written before declaring the change finished, in the same session that made the change.
- Existing change-log files are never edited after the fact. A correction is a new entry referencing the old one.
- [docs/DECISIONS.md](DECISIONS.md) is the source of truth for decisions. Agents never modify its existing entries and never append to it on their own: propose in the change log, wait for explicit validation from Juan or the developer, then append.
