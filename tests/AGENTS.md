# AGENTS.md — /tests

Guidance for coding agents (and humans) writing tests in this repo.

## Goals

- **Simple, readable and maintainable tests** that validate **behavior**.
- Cover the **happy path + key edge cases**.
- **Mock only what’s expensive / unstable / external** (network, filesystem outside `tmp_path`, time, randomness, DB, cloud SDKs).
- Avoid “mocking the universe” — over-mocking makes tests brittle and meaningless.
- Prefer testing the **public entrypoint** (public function/method), not private helpers.
- 
---

## What “good” looks like

### Test types we want
- **Unit tests (default):** small surface area, fast, minimal setup for.
- **Thin integration tests (sometimes):** e.g., a real parser + real sample payload, or a real `pydantic` model validation path — still fast, no external services.

### What we don’t want
- Mocks for every function call “because we can”.
- Tests asserting internal implementation details (call counts, exact private method order) unless it’s truly critical.
- Giant fixtures that build 20 objects when you need 2.

---

## Project conventions

### File + test naming
- Files: `test_*.py`
- Tests: `def test_<what>_<when>_<then>():`
- Group by feature/module mirroring source structure:
  - `tests/<package_or_module>/test_<thing>.py`

### Style
- Use **Arrange → Act → Assert**.
- Prefer **plain asserts**; only use `pytest` helpers when it improves clarity or when necessary.
- Keep a test under ~30–40 lines unless there’s a strong reason. Its easier to read and maintain small tests.

---

## Pytest patterns to prefer

### Parametrize for coverage (instead of copy-paste)
Use `@pytest.mark.parametrize` for:
- input variations
- edge cases (empty, None, invalid, boundary values)
- error handling cases (different invalid inputs → different exceptions)

### Use `tmp_path` for files
- Write temp files under `tmp_path` only.
- Never depend on a developer machine path.

### Use fixtures, but don’t overdo it
- Fixtures should be **small** and **focused**.
- Prefer `scope="function"` by default but use `module` or `session` if setup is expensive and state is immutable.
- Keep fixtures in `conftest.py` only if they are shared across multiple test files.
- Prefer local fixtures in the test file for clarity.
- If a fixture becomes “mini app factory”, it’s probably too big.

### Exceptions
- Validate failures with `pytest.raises(...)`.
- Not needed to assert on entire text dumps.

---

## Error handling tests (required)

If code **documents** error behavior (docstring “Raises:” section, comments), tests must validate it.

### Rules
- For every documented exception path, write **at least one test** that triggers it.
- Assert the **exception type**

### Exception mapping
If the module catches a low-level exception and re-raises a domain exception, tests must prove the mapping:
- source error triggers
- domain error is raised
- cause is preserved when relevant (`raise X from e`)

Example expectations:
- `with pytest.raises(DomainError, match="invalid config"):` …
- `assert exc_info.value.__cause__ is not None` (only if the code uses exception chaining)
- Pydantic: `with pytest.raises(ValidationError) as exc_info:` then `exc_info.value.errors()` contains expected locations.

### Don’t overfit
- Don’t assert full error strings (they change easily).
- Don’t assert exact traceback text.
- Use small, stable message fragments or structured error details.

---

## Mocking rules (important)

### Mock these (usually)
- Network calls (HTTP clients, SDK calls)
- Time (now/utcnow/sleep)
- Randomness
- External systems (DB, queues, cloud storage)
- Expensive compute or side-effectful things
- Very complex dependencies that are out of scope for the unit test

### Don’t mock these (usually)
- Pure functions
- Simple transforms / formatting
- `pydantic` validation (prefer to use real models / validation)
- Your own code boundaries unless there’s a real external dependency behind it

### If you mock, mock at the boundary
- Patch the **public boundary** your code calls (e.g., `requests.get`, `Client.fetch`, `Repo.save`), not 15 internal helper functions.
- Prefer **fakes/stubs** over deep mocks when possible.

✅ Good: “fake repository” in-memory dict  
❌ Bad: mocking 10 repo methods and asserting call order

---

## Edge cases checklist (use this)

When writing tests for a function/class, try to include:
- Empty inputs (empty list/string/dict)
- Null-ish inputs (None) if allowed
- Boundary values (0, 1, max, min)
- Invalid types/values (and correct error behavior)
- Duplicates / ordering (if relevant)
- Missing keys / extra keys (for dict-like input)
- Unexpected but realistic input shape (e.g., API payload variants)
- Error paths documented in docstrings (“Raises:”)

---

## Data-driven tests

- Prefer small inline examples.
- If payloads are big, store under `tests/data/` as `.json` / `.csv` and load them.
- Keep test data minimal but realistic.

---

## Common tools (use only if needed)

- `monkeypatch` for env vars / patching functions.
- `capsys` for stdout/stderr.
- `caplog` for logging assertions (only if required).
- Time control: use what the repo already uses (e.g., `freezegun`, `time_machine`), otherwise `monkeypatch`.
- HTTP mocking: use what the repo already depends on (e.g., `responses`, `requests-mock`, `respx`). Don’t introduce new libs casually.

---

## What to assert

Prefer asserting:
- Returned value structure/content
- State changes (files created in `tmp_path`, in-memory fake repo updated, attribute changed)
- Raised errors for invalid cases (especially documented ones)
- Stable, user-visible outputs

Avoid asserting:
- Logging text (unless required)
- Internal function call sequences
- Private attributes (unless it’s a data container by design)

---

## Running tests

- Standard: `pytest tests/` - Runs all tests in `tests/` folder.
- Targeted: `pytest tests/module/test_file.py::test_function_name` - Run specific test.
- Common options:
  - `pytest -q` (quiet)
  - `pytest -k <pattern>` (filter)
  - `pytest -x` (stop on first fail)

### UV or Poetry
- If using `uv`: `uv run pytest tests/`
- If using `poetry`: `poetry run pytest tests/`
- 
---

## Quick “agent” workflow

1. Identify the unit under test (public function/class method).
2. Write 1 happy-path test.
3. Add 2–5 parametrized edge-case tests.
4. Add failure-mode tests for **every documented exception** (`Raises:`).
5. Mock only external boundaries; keep mocks minimal.
6. Keep tests fast, simple and deterministic.