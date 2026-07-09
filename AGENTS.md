# Repo rules

All rules for modifying this repo live in dedicated documents under `docs/`. Read the relevant one before acting. This file is only an index and must stay small: a new rule category means a new document plus one line here.

- [docs/HOW_TO_WRITE_DOCUMENTS.md](docs/HOW_TO_WRITE_DOCUMENTS.md): writing style for every document, comment, and message. Never use em-dashes.
- [docs/HOW_TO_COMMIT.md](docs/HOW_TO_COMMIT.md): commit rules. Never include AI/agent attribution.
- [docs/HOW_TO_VALIDATE.md](docs/HOW_TO_VALIDATE.md): every change must pass ruff (format + check), ty, and pytest before it is finished.
- [docs/HOW_TO_LOG_CHANGES.md](docs/HOW_TO_LOG_CHANGES.md): every change writes an entry in `change-logs/` before it is finished.
- [docs/DECISIONS.md](docs/DECISIONS.md): source of truth for decisions, biases, and tradeoffs. Never modify or extend it without explicit validation from Juan or the developer.
- [docs/plans/](docs/plans/): detailed phase plans. Work follows the plan of the active phase.
