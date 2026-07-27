# Contributing to finlib

## Setup

```bash
git clone https://github.com/simone-belli/finlib
cd finlib
poetry install --with dev
pre-commit install && pre-commit run --all-files
```

## Quick start

See `README.md`.

## How to contribute

1. Branch off the main branch.

2. Commit using conventional commits.

3. Create a PR.

    - Fill the PR description following the template.

    - CI must go green

    - Branch protection prevents direct pushes to main.

## Testing & Quality

### Principles

- unit tests to test behaviour
- hypothesis tests to test invariants
- fake what we own; mock what we don't

### Full suite with coverage (pytest)

pytest + pytest-asyncio; property-based tests (Hypothesis) for portfolio invariants and position sizing

```bash
poetry run pytest --cov=finlib -v
```

### Type-checking (mypy)

```bash
poetry run mypy src/ --strict
```

### Linting (ruff)

Extended checks: E,F,I,B,UP,SIM,RET.

```bash
poetry run ruff check src/ tests/ script/
```

### pre-commit

Enforcement of linting, format, mypy --strict.

### CI

CI enforces ≥85% pytest coverage, mypy --strict, and ruff on every push.
