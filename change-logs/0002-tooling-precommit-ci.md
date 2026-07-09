# 0002: Tooling, pre-commit, and CI

Date: 2026-07-09
Author: agent session (Juan directing)

## What changed

Phase 0, step 1. Set up the development toolchain and the machinery that
enforces the validators mechanically.

- `pyproject.toml`: added runtime deps (`pydantic`, `pydantic-settings`,
  `pyyaml`) and a dev dependency group (`ruff`, `pytest`, `ty`, `pre-commit`).
  Added `[tool.ruff]`, `[tool.ruff.lint]`, `[tool.pytest.ini_options]` (with
  `pythonpath = ["."]` so first-party packages import in tests, and a `slow`
  marker for later phases), and `[tool.ty.environment]`.
- `edge/config.py`: `CameraConfig` (pydantic-settings) that reads the camera
  connection from `.env` with the `CAMERA_` prefix, plus a `rtsp_url` property
  and a `load_camera_config()` helper.
- `.pre-commit-config.yaml`: local hooks mirroring the four validators
  (`ruff format`, `ruff check`, `ty check`, `pytest`) plus an em-dash guard
  (pygrep) on markdown files, excluding `docs/HOW_TO_WRITE_DOCUMENTS.md`.
- `.github/workflows/ci.yml`: the same four validators on every push to `main`
  and on pull requests, via `astral-sh/setup-uv`.
- `tests/test_config.py`: three tests for the config loader, isolated from the
  developer's local `.env`.
- Deleted the root hello-world `main.py`.

Pre-existing issue fixed in passing: `docs/plans/PHASE_0.md` line 49 contained a
literal em-dash while describing the guard. The writing rule bans the character
outside the doc that defines it, so the line now names the character instead of
printing it. Without this the new guard fails on the repo's own plan.

## Why

Every later step depends on this toolchain and on the hooks that stop a
non-passing change from landing. Doing it first makes the rule in
HOW_TO_VALIDATE mechanical rather than a matter of memory.

## Files created / modified / deleted

- Created: `edge/config.py`, `.pre-commit-config.yaml`,
  `.github/workflows/ci.yml`, `tests/test_config.py`,
  `change-logs/0002-tooling-precommit-ci.md`.
- Modified: `pyproject.toml`, `uv.lock` (from `uv sync`),
  `docs/plans/PHASE_0.md` (em-dash fix), `src/main.py` (ruff reformatted one
  string; no behavior change, `src/` is removed in step 9),
  `change-logs/INDEX.md`.
- Deleted: `main.py` (root hello-world stub).

## Validation

Run from the repo root:

- `uv sync`: succeeded, dev group installed (ruff 0.15.21, pytest 9.1.1,
  ty 0.0.57, pre-commit 4.6.0).
- `uv run ruff format .`: pass (all files unchanged after the initial format).
- `uv run ruff check .`: pass.
- `uv run ty check`: pass.
- `uv run pytest`: pass (3 passed).
- `uv run pre-commit run --all-files`: all five hooks pass.
- Guard rejection verified: a markdown file containing an em-dash makes the
  `no-em-dash` hook fail with exit code 1, pointing at the line.
- `uv run pre-commit install`: hook installed at `.git/hooks/pre-commit`.

CI green on GitHub is verified after the push, not in this entry.

## Suppressions

One `# ty: ignore[missing-argument]` on `load_camera_config()` in
`edge/config.py`. `ty` does not model that a pydantic-settings `BaseSettings`
fills its required fields from the environment at construction, so it reports a
false positive on the zero-argument call. Justified here per HOW_TO_VALIDATE.
This is exactly the ty maturity risk noted in D-007; the fallback to mypy stays
available if these accumulate.

## Decisions, biases, tradeoffs

- Applies D-007 (uv + ruff + pytest + ty), still `proposed`. Implementing this
  step acts on it. It needs validation from Juan or the developer in
  DECISIONS.md; this entry does not modify that file.
- No new decision proposed.
