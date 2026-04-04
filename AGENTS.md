## Purpose

This file is for agentic coding agents working in `myskoda`.
It documents the repository's real development workflow, code style, and guardrails.
Prefer small, targeted changes that fit existing patterns.

## Project Overview

- Language: Python, with the exact minimum version specified in `pyproject.toml`
- Package manager and environment tool: `uv`
- Dependencies, build backend, etc are specified in `pyproject.toml`
- Main package: `myskoda/`
- Tests: `pytest`
- Lint and formatting: `ruff` and `ruff format`
- Type checking: `pyright`
- Commit hooks: `pre-commit`

## Repository Layout

- `myskoda/`: library source
- `myskoda/auth/`: auth flow and token handling
- `myskoda/models/`: response models and enums
- `myskoda/cli/`: CLI entrypoints and helpers
- `tests/`: unit tests and fixtures
- `fixtures/`: additional fixture material
- `docs/`: documentation sources
- `scripts/`: helper scripts

## Setup

Use the repository's preferred workflow:

```bash
uv venv
source .venv/bin/activate
uv sync --all-extras
```

## Build, Lint, Typecheck, Test

Run commands from the repository root.

### Install dependencies

```bash
uv sync --all-extras
```

### Lint and format

```bash
uv run ruff check .
uv run ruff format .
```

### Type checking

```bash
uv run pyright
```

### Run pre-commit checks

This matches CI and local contributor guidance:

```bash
uv run pre-commit run --hook-stage manual --all-files
```

### Run the full test suite

Fast local run:

```bash
uv run pytest
```

CI-style run with coverage:

```bash
uv run pytest --cov-report term --cov-report xml:coverage.xml --cov=myskoda
```

### Run a single test file

```bash
uv run pytest tests/test_utils.py
```

### Run a single test function

```bash
uv run pytest tests/test_utils.py::test_async_debounce
```

### Run tests by keyword expression

```bash
uv run pytest -k debounce
```

### Run a single async-heavy test with logs visible

Pytest logging is already enabled in `pyproject.toml`, so this is often enough:

```bash
uv run pytest tests/test_rest_api.py::test_get_info
```

## Release and Packaging

- Build metadata is defined in `pyproject.toml`
- The package version is dynamic
- Do not hand-edit version strings unless the repository workflow changes

## CI Facts

The GitHub workflow in `.github/workflows/test.yaml` currently does this:

- `uv sync --all-extras`
- `uv pip install pre-commit`
- `uv run pre-commit run --hook-stage manual --all-files`
- `uv run pytest --cov-report term --cov-report xml:coverage.xml --cov=myskoda`

Prefer validating with the same commands before finishing substantial changes.

## Code Style

Follow the existing code, not generic Python advice.

### Formatting

- Line length is `100`
- Target runtime is Python `3.13`
- Use `ruff format` for formatting
- Keep code ASCII unless the file already requires Unicode
- Preserve existing blank-line and docstring patterns where practical

### Imports

- Keep imports grouped in the existing order: standard library, third-party, local package
- Use direct imports rather than lazy imports unless there is a concrete reason
- Prefer explicit imports over wildcard imports
- In-package imports use both absolute and relative style today; follow the surrounding file's pattern
- Avoid introducing unused imports just to satisfy speculative future work

### Typing

- Add type hints for new public functions, methods, and important internal helpers
- Use modern built-in generics like `list[str]`, `dict[str, Any]`, `tuple[int, ...]`
- Use union syntax like `Foo | None` instead of `Optional[Foo]`
- Use `collections.abc` types for callable and iterator contracts when appropriate
- The codebase already uses `ParamSpec`, `Protocol`, `Self`, and generic dataclasses; reuse those patterns when helpful
- Respect `pyright`; do not add ignore comments unless necessary and justified by surrounding code
- Match the file's existing annotation density rather than over-annotating trivial locals

### Naming

- Classes use `PascalCase`
- Functions, methods, variables, and modules use `snake_case`
- Constants use `UPPER_SNAKE_CASE`
- Enum members follow the style already present in each enum
- Test files are named `test_*.py`
- Test functions are named `test_*`
- Prefer descriptive domain names such as `authorization`, `charging_profile`, `vehicle_status`, `target_vin`

### Docstrings

- Ruff enforces pydocstyle with the Google convention
- Public modules, classes, and functions usually have docstrings
- Tests are exempt from docstring linting, but many tests still include useful docstrings
- Keep docstrings short and factual
- Do not add noisy comments that restate obvious code

### Data Models and Enums

- This project leans heavily on typed response models under `myskoda/models/`
- Reuse existing model classes and enums before adding new string literals or ad hoc dict parsing
- Prefer extending the existing model layer instead of returning partially structured dicts
- When API values are enumerated, prefer `StrEnum` or the existing enum abstractions already used in the package

### Async Conventions

- The library is async-first; many public APIs are `async def`
- Preserve async boundaries instead of wrapping async behavior in sync helpers
- Use `await` directly rather than storing unnecessary intermediate coroutines
- Follow the repository's use of `asyncio.timeout(...)` for request timeout handling
- When scheduling background work, be explicit and consistent with existing task-management patterns
- Tests for async code typically use `@pytest.mark.asyncio`

### Error Handling

- Prefer specific exception types over broad `except Exception`
- Log context before re-raising when the existing code does so
- Raise domain-specific errors when the project already defines one for that condition
- Preserve existing error propagation unless the task requires changing behavior
- Chain exceptions with `raise ... from err` when translating lower-level failures
- Avoid swallowing network/auth failures silently

### Logging

- Use module-level loggers via `logging.getLogger(__name__)`
- Keep log messages concise and operationally useful
- Prefer structured context in format arguments instead of f-strings in logger calls
- Use `debug` for verbose request/response detail, `info` for high-level lifecycle events, and `warning` for deprecated or suspicious usage

### Testing Style

- Add or update tests for behavior changes
- Prefer extending existing fixture-driven tests over building a totally new test harness
- Reuse `tests/conftest.py` fixtures where possible
- Use `aioresponses` for HTTP mocking, matching current tests
- Keep test data in fixtures when behavior depends on realistic API payloads
- Assert behavior and parsed values, not just that code paths execute
- Avoid unnecessary sleeps in tests unless validating debounce/timing behavior

### HTTP and API Work

- Route all API calls through `RestApi` patterns already present in `myskoda/rest_api.py`
- Keep URL construction consistent with existing endpoint methods
- Preserve anonymization support where that pattern already exists
- Deserialize responses through existing model constructors such as `from_json`
- Avoid duplicating request boilerplate if a nearby helper already handles it

### CLI Work

- The CLI is optional via the `cli` extra
- Keep CLI-specific behavior under `myskoda/cli/`
- Avoid pulling CLI-only dependencies into core library code
- Respect existing separation between library behavior and command presentation

## Ruff Configuration Notes

Ruff runs with `select = ["ALL"]`, so assume strict linting.
Some rules are intentionally ignored in `pyproject.toml`, including:

- missing trailing comma
- some pydocstyle layout rules
- boolean positional argument lint
- TODO-link enforcement
- `print` usage
- assert usage in tests

Even with these ignores, prefer clean code that would pass strict linting without relying on exceptions.

## File-Specific Expectations

- `tests/*` and `**/test_*.py` ignore docstring lint rules
- `myskoda/cli/*` also ignores docstring lint rules
- Coverage omits `myskoda/cli/*`

## Change Strategy For Agents

- Read the surrounding file before editing
- Prefer the smallest correct patch
- Do not refactor unrelated code while fixing a focused issue
- Do not invent compatibility layers without a concrete need
- If adding a new abstraction, keep it justified and local
- Preserve public API behavior unless the task explicitly changes it

## Validation Expectations

For small changes, run the narrowest useful validation:

- changed utility code: targeted pytest file or test function
- changed API/model behavior: targeted tests covering that endpoint/model
- changed shared or cross-cutting behavior: full `uv run pytest`

For substantial changes, prefer this sequence:

```bash
uv run ruff check .
uv run ruff format .
uv run pyright
uv run pytest
```

## Commit Guidance

- Follow Conventional Commits as documented in `CONTRIBUTING.md`
- Format: `<type>(optional scope): <short description>`
- Common types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## Practical Reminders

- Use `uv run ...` so commands execute in the project environment
- Do not assume internet access or live Skoda credentials during tests
- Be careful with fixture updates; they often encode contract expectations
- If you change request/response behavior, inspect both source and tests before finalizing
