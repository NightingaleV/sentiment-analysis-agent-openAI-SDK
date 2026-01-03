# Agent Instructions & Repository Guidelines

## Persona
You are a Senior Python Developer specializing in Data Engineering and ML. You write clean, typed, modular code using modern Python 3.12+ features. You prefer Pydantic for validation and strictly adhere to project conventions.

## Project Context
Agentic stock analysis system.
- **Core:** Python 3.12, UV (dependency management).
- **Data:** Pydantic 2.0 (validation), Pandas (manipulation).
- **Network:** Httpx (async).
- **Testing:** Pytest, Mocks.

## Workflow & Commands
**Always use `uv` to run commands.**

### Installation
- Sync dependencies: `uv sync`
- Sync dev dependencies: `uv sync --group dev`

### Testing
- **Run All Tests:** `uv run pytest`
- **Run Single Test (Preferred):** `uv run pytest tests/test_sentiment_pipeline.py`
- **Run Specific Test Case:** `uv run pytest tests/test_sentiment_pipeline.py::test_specific_case`
- **Run with Coverage:** `uv run pytest --cov=sentiment_analysis_agent`
- **Integration Tests:** `uv run pytest -m integration`

### Code Quality
- **Format (Write):** `uv run black --line-length 120 .`
- **Lint (Read):** `uv run pylint sentiment_analysis_agent`

## Code Style Guidelines

### 1. Formatting & Structure
- **Line Length:** 120 characters.
- **Indentation:** 4 spaces.
- **Quotes:** Double quotes `"`.
- **Files:** Ends with a newline.

### 2. Imports
- **Sorting:** Standard Library -> Third Party -> Local Application.
- **Style:** Absolute imports preferred over relative.
- **Prohibited:** `from module import *`.

### 3. Type Hints (Strict)
- **Version:** Python 3.12+ syntax.
- **Generics:** Use built-in types (`list[str]`, `dict[str, Any]`, `tuple[int, int]`).
- **Unions:** Use `|` operator (`str | None`, `int | float`).
- **No `typing` module:** Avoid `List`, `Dict`, `Optional`, `Union` from `typing`.
- **Return Types:** Mandatory for all functions/methods.

### 4. Naming Conventions
- **Classes:** `PascalCase` (e.g., `SentimentScorer`).
- **Functions/Variables:** `snake_case` (e.g., `calculate_impact`).
- **Constants:** `UPPER_CASE` (e.g., `DEFAULT_TIMEOUT`).
- **Private Members:** `_leading_underscore` (e.g., `_validate_input`).

### 5. Documentation (Docstrings)
- **Style:** Google Style.
- **Coverage:** Required for all public modules, classes, and methods.
- **Content:**
    - First line: Imperative summary (e.g., "Fetch the latest news.").
    - **No Type Duplication:** Do NOT include types in `Args:` or `Returns:` sections (types are in signatures).
    - **Example:**
      ```python
      def fetch_data(ticker: str, limit: int = 10) -> list[dict]:
          """Fetch financial data for a ticker.

          Args:
              ticker: Stock symbol.
              limit: Max items to return.

          Returns:
              List of data dictionaries.
          """
      ```

### 6. Error Handling
- **Exceptions:** Use specific exceptions (e.g., `ValueError`, `NetworkError`).
- **Avoid:** Bare `except:` clauses.
- **Pattern:** Fail fast. Validate inputs early (often via Pydantic).

### 7. Pydantic Usage
- Use `Field(description="...")` for all public model fields to aid LLM understanding.
- Use `ConfigDict(extra="forbid")` by default.
- Use `@field_validator` and `@model_validator` for logic.

## Architecture Patterns
- **Agents (`/agents`):** Logic for LLM interaction. Return Pydantic models.
- **Models (`/models`):** Shared Pydantic data structures.
- **Data Services (`/data_services`):** External API wrappers. Inherit from `BaseSentimentSource`.
- **Pipeline (`/pipeline`):** Core business logic and transformations.

## Git & Commit Standards
**Format:** `<type>: <description>`

- **Types:**
    - `feat`: New feature
    - `fix`: Bug fix
    - `refactor`: Code change that neither fixes a bug nor adds a feature
    - `docs`: Documentation only
    - `test`: Adding or correcting tests
    - `chore`: Maintenance (deps, config)

**Example:** `feat: add heuristic scoring for news relevance`

