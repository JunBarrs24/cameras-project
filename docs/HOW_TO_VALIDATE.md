# How to validate changes

Every change must pass all validators before it is considered finished. "Finished" also includes writing the change-log entry (see [HOW_TO_LOG_CHANGES.md](HOW_TO_LOG_CHANGES.md)).

## Commands

Run from the repo root, all four, in this order:

```bash
uv run ruff format .        # formatter
uv run ruff check .         # linter
uv run ty check             # typechecker (see docs/DECISIONS.md, D-007)
uv run pytest               # tests
```

The tooling is added to `pyproject.toml` in Phase 0, step 1. If `ty` blocks work with false positives, the fallback is `mypy`; that switch requires a new validated entry in DECISIONS.md.

## Pre-commit

The same validators run as pre-commit hooks (`.pre-commit-config.yaml`, set up in Phase 0 step 1), plus an em-dash guard on markdown files enforcing the writing rule. After cloning:

```bash
uv run pre-commit install
```

Committing with `--no-verify` requires a written justification in the change-log entry. CI (`.github/workflows/ci.yml`) runs the same four validators on every push, so the rule holds even outside a hooked clone.

## Rules

- All four must pass. Any failure blocks completion of the change.
- Never silence a diagnostic to make it pass (`# noqa`, `# type: ignore`, `pytest.mark.skip`) without a written justification in the change-log entry.
- New logic requires tests (zone math, rules, schemas, parsers). Pure wiring can be covered by an integration test.
- A validator failing for a pre-existing reason unrelated to the change is reported in the change log, never hidden. Fix it in its own change if small.
- Results are reported honestly: if something is left red, the change log carries the failing output and the reason.
