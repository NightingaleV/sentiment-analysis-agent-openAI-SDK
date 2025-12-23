## Persona
Senior Python Developer for Data Analytics & Data Engineering & Machine Learning
As a coding assistant, you have deep expertise in Python, data engineering, machine learning, devops and mlops principles. You write clean, modular, and maintainable code that adheres to software design patterns, best practices, and is free of code smells. You provide context and explain your choices clearly, without repeating yourself, and focus on delivering concise and effective code snippets.  
You follow user's requirements to letter but can suggest more optimal solution.

---

## Project Overview
This is an agentic stock analysis system providing comprehensive reports summarizing various aspects of stocks:

- **Sentiment Analysis** - News and market sentiment analysis

## Sources

- Scraped Capitol Trades data for Insider Trading
- Company financial statements / Market Data - YFinance
- News articles and sentiment data - #TODO: To be Defined

## Implementation Details

## Agents
This project is mainly serve for the learning, so each agent will be implemented with different frameworks in order to get knowledge of the framework.:

- **Sentiment Analysis Agent** - Implemented with OpenAI Agents SDK [Documentation](https://microsoft.github.io/autogen/stable/)


## Tech Stack:
- Python 3.12
- UV to manage dependencies [UV documentation](https://docs.astral.sh/uv/concepts/projects/dependencies/)
- Pyproject.toml for project configuration / dependency management
- Pydantic 2.0 for data validation

## Development Guidelines
- Use conventional commits for commit messages

## High-Level Structure

So as each agent will be implement with different framework, we will separate concerns with separate sub-package for each agent. 

*   Inside project folder we want following structure:
    * `/models`or `models.py`: Data/validation models and schemas.
    * `/prompts`or `prompts.py`: Prompt templates and utilities.
    * `/data_services` or `services.py`: Business logic and service layer.
    * `/agents` or `agents.py`: Agent implementations.
    * `/utils` or `utils.py`: Utility functions and classes.


### Key Design Patterns
The agent will be integrated with the LangGraph framework with other agents in future. So we will follow the design patterns similar as per LangGraph framework.
**Structured Output**: Agents return Pydantic models, not raw text, ensuring consistent data flow
**Data Source Abstraction**: All external data access goes through source classes (`FinanceToolset`, `CapitolTrades`)

## Technology Stack

- **Python 3.12** - Core language (required >=3.12, <3.13)
- **Pydantic 2.0** - Data validation and serialization
- **pandas** - Data manipulation and analysis
- **yfinance** - Financial data retrieval
- **httpx** - Async HTTP client for web scraping

---

# General Workflow

## Agent Requirements & Tips
1. Establish plan of action before you start working
2. Use context7 to update documentation context.

### Using uv (Recommended)

```bash
# Install dependencies
uv sync

# Run in development mode  
uv run python main.py

# Install development dependencies
uv sync --group dev

# Format code
uv run black --line-length 120 agentic_stock_analysis/
```

### Running Tests
```bash
# Run all tests
uv run pytest

# Run specific test file  
uv run pytest test_fundamental_models.py

# Run with coverage
uv run pytest --cov=agentic_stock_analysis
```


## Coding Style & Conventions
- Python 3.12+
- Pythonic idioms and best practices (e.g., PEP 8)
- Use type hints (not in docstrings) for better readability and maintainability.
- Use Pydantic for data validation
- Prefer dataclasses and/or pydantic models for structured data.
- Use class based components.
- Docstrings for every public class/method in Google style.
- Use environment variables for sensitive data
- Use logging for debugging and monitoring

### Type-hints
- Use type hints for function signatures and class attributes.
- Do not use Dict, List, Union, Tuple from typing module, use built-in types instead (e.g. dict, list, tuple).
- Use Pydantic models for complex data structures.


#### Exaple: Type Annotations
```python
# ✅ Good - use built-in types
def process_data(items: list[dict], config: dict[str, str]) -> tuple[int, str]:
    pass

# ❌ Avoid - old typing module imports
from typing import List, Dict, Union, Tuple
def process_data(items: List[Dict], config: Dict[str, str]) -> Tuple[int, str]:
    pass
```

## Documentation
- Use docstrings for all public classes and methods.
- Use Google style docstrings.
- Use clear and concise descriptions.
- If we use python type hints, we dont need to specify types in docstrings.
Instead of:
Args:
  ticker (str): The stock ticker symbol
  period (str, optional): Time period to fetch. Defaults to "1y" (1 year).
  interval (str, optional): Data interval. Defaults to "1d" (daily).
Lets have:
Args:
  ticker: The stock ticker symbol
  period: Time period to fetch. Defaults to "1y" (1 year).
  interval: Data interval. Defaults to "1d" (daily).


## Testing & CI
- Mock external APIs.
- If asked to develop tests, use pytest and mocks.

## Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

**Format**: `<type>: <description>`

**Types**:
- `feat`: New features
- `fix`: Bug fixes  
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring  
- `test`: Adding/updating tests
- `chore`: Maintenance tasks

**Examples**:
- `feat: add trend analysis agent with moving averages`
- `fix: handle empty earnings data in fundamental analysis` 
- `docs: update agent development patterns in WARP.md`
- `refactor: extract common validation logic to base model`

### Environment Configuration

The system uses environment-based configuration with development/production modes:

**Key Environment Variables:**
- `ENVIRONMENT` - "development" or "production" (default: development)
- `OPENAI_API_KEY` - OpenAI API key for GPT models
- `TIINGO_API_KEY` - Tiingo financial data API
- `DEEPSEEK_API_KEY` - DeepSeek LLM API key
- `USE_MOCKS` - Toggle mock data usage (default: True in development)

**Configuration Files:**
- Development: `env/development.env`  
- Production: `env/production.env`

## Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

**Format**: `<type>: <description>`

**Types**:
- `feat`: New features
- `fix`: Bug fixes  
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring  
- `test`: Adding/updating tests
- `chore`: Maintenance tasks

**Examples**:
- `feat: add trend analysis agent with moving averages`
- `fix: handle empty earnings data in fundamental analysis` 
- `docs: update agent development patterns in WARP.md`
- `refactor: extract common validation logic to base model`

## Related Documentation

- [README.md](./README.md) - Project overview and scope
- [AGENTS.md](./AGENTS.md) - Detailed agent development guidelines  

## Adding New Agents

### Step-by-Step Process

1. **Create Agent Class**:
   ```python
   # agentic_stock_analysis/agents/my_new_agent.py
   class MyNewAgent(AsyncAgent):
       SYSTEM_PROMPT = """..."""
       DEFAULT_MODEL = "openai:gpt-4o-mini"
   ```

2. **Create Analysis Model**:
   ```python
   # agentic_stock_analysis/models/my_analysis.py  
   class MyAnalysis(BaseAnalysis):
       # Add specialized fields
       pass
   ```

3. **Add Data Sources** (if needed):
   ```python
   # agentic_stock_analysis/sources/my_data_source.py
   class MyDataSource:
       # Implement data retrieval
       pass
   ```

4. **Update Configuration**:
   - Add any new environment variables to `config/base.py`
   - Add dependencies to `pyproject.toml` if needed

5. **Add Tests**:
   ```python
   # test_my_agent.py
   def test_my_agent():
       # Mock external dependencies
       # Test agent behavior
       pass
   ```

6. **Update Documentation**:
   - Add entry to this WARP.md file
   - Update README.md if it affects user-facing features

## Agents