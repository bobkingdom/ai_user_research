# CLAUDE.md

## 核心编程原则  

- 以瞎猜接口为耻，以认真查询为荣 
- 以模糊执行为耻，以寻求确认为荣 
- 以臆想业务为耻，以人类确认为荣
- 以创造接口为耻，以复用现有为荣
- 以跳过验证为耻，以主动测试为荣 
- 以破坏架构为耻，以遵循规范为荣
- 以假装理解为耻，以诚实无知为荣
- 以盲目修改为耻，以谨慎重构为荣
- 以每次编码完成就结束为耻，以步步为营复盘每一步编码疏漏为荣

## 工作原则
1.方案讨论优先 -先讨论清楚方案，直到达成一致，不要直接开始编码
2.AI 能力优先 - 优先考虑发挥AI能力的方案(mor e intelligence, less structure)，能用Prompt 搞定就不搞自己的工程代码
3.根因分析 - 收到问题反馈时，要优先思考背后原因不要做定向优化
4.时间上下文 -Prompt 都要加入时间上下文架构设计理念

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered user research platform demonstrating three Agent frameworks (Claude Agent SDK, Agno, SmolaAgents) implementing four research scenarios.

**Framework Assignments:**
- **Claude Agent SDK**: 1-on-1 audience interviews (Agentic Loop + MCP)
- **Agno Framework**: Batch survey deployment (Teams) + Focus group sessions (Workflows)
- **SmolaAgents**: Audience persona generation pipeline (Manager pattern)

## Development Commands

### Running the service

```bash
# Development mode (with hot reload)
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn src.main:app --host 0.0.0.0 --port 8000

# Via start script
./start.sh
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_survey.py

# Run async tests
pytest -v tests/
```

### Code Quality

```bash
# Format code (Black)
black src/ tests/ --line-length 120

# Lint (Ruff)
ruff check src/ tests/

# Type checking (MyPy)
mypy src/
```

### Environment Setup

```bash
# Create virtual environment
python -m venv venv

# Activate (macOS/Linux)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install dev dependencies
pip install -e ".[dev]"
```

## Architecture Overview

### Directory Structure

```
src/
├── agents/              # Individual agent implementations
│   ├── survey_agent.py           # Agno-based survey responder
│   ├── focus_group_agent.py      # Agno-based focus group participant
│   └── generation_agents.py      # SmolaAgents managed agents
│
├── workflows/           # Multi-agent orchestration
│   ├── survey_deployment.py      # Agno Teams for batch surveys (100-500 concurrency)
│   └── focus_group_workflow.py   # Agno Workflows for focus groups
│
├── pipelines/           # Complex multi-step processes
│   ├── audience_generation_pipeline.py    # SmolaAgents Manager pattern
│   └── batch_generation.py                # Batch persona generation
│
├── scenarios/           # High-level scenario implementations (future)
│   ├── interview/      # Claude Agent SDK + MCP tools
│   ├── survey/         # Agno Teams batch deployment
│   ├── focus_group/    # Agno Workflows orchestration
│   └── generation/     # SmolaAgents pipeline
│
├── core/                # Shared data models and prompts
│   ├── models.py       # Pydantic models (AudienceProfile, SurveyDefinition, etc.)
│   └── prompts.py      # Unified prompt templates
│
├── utils/               # Utilities
│   ├── concurrency.py   # Async concurrency control (semaphore-based)
│   ├── task_manager.py  # Task deduplication and polling
│   └── error_handler.py # Retry logic with exponential backoff
│
└── main.py              # FastAPI application
```

### Core Data Models (src/core/models.py)

All data models use Pydantic. Key models:

- **AudienceProfile**: Complete persona with demographics, professional, personality, lifestyle
- **SurveyDefinition**: Survey structure with questions (single_choice, multiple_choice, open_ended)
- **FocusGroupDefinition**: Focus group setup with SPIN framework questions
- **SurveyResponse**: Individual survey answers
- **DeploymentResult**: Batch operation results with success/failure tracking

### Agent Framework Patterns

**Agno (Survey & Focus Group)**:
- Use `agno.Agent` with `ModelSettings(id=model_id)`
- Teams for parallel execution: `Team(agents=agents)` → `team.run_parallel()`
- Workflows for sequential steps with state passing
- Max concurrency: Surveys (100), Focus Groups (50)

**SmolaAgents (Persona Generation)**:
- Manager + Managed Agents pattern
- Use `ToolCallingAgent` for both manager and managed agents
- Managed agents defined with `ManagedAgent(agent=..., name=..., description=...)`
- Manager coordinates via `managed_agents` parameter
- Tools defined with `@tool` decorator (not used in current pipeline architecture)

**Claude Agent SDK (Future - 1-on-1 Interviews)**:
- Agentic Loop: think → act → observe
- MCP tools integration for web search, memory storage
- Multi-turn conversation with context management
- SPIN framework (Situation, Problem, Implication, Need-Payoff) for interviews

### Concurrency Management

**ConcurrencyManager** (src/utils/concurrency.py):
- Semaphore-based limiting
- `ConcurrencyManager.for_survey()`: 100 max concurrency
- `ConcurrencyManager.for_focus_group()`: 50 max concurrency
- Batch execution: `execute_batch(tasks, max_concurrency)`

**TaskManager** (src/utils/task_manager.py):
- Prevents duplicate tasks via fingerprinting
- `get_or_create_task(task_key, task_params)` returns (task, is_new)
- Supports polling for long-running tasks

### Error Handling

**ErrorHandler** (src/utils/error_handler.py):
- 3 retries max with exponential backoff
- `with_retry(func, *args, **kwargs)` wrapper
- Isolated batch execution: single failure doesn't break entire batch
- Rate limit error handling with backoff

## Environment Variables

Required:
- `OPENROUTER_API_KEY`: OpenRouter API key (recommended)
- `OPENROUTER_API_URL`: https://openrouter.ai/api/v1

Optional:
- `ANTHROPIC_API_KEY`: Anthropic API key
- `OPENAI_API_KEY`: OpenAI API key
- `SURVEY_MAX_CONCURRENCY`: Survey concurrency limit (default: 100)
- `FOCUS_GROUP_MAX_CONCURRENCY`: Focus group concurrency limit (default: 50)
- `LOG_LEVEL`: Logging level (default: INFO)

## API Configuration

**Model IDs**:
- Agno agents: `"claude-3-5-sonnet-20241022"`
- SmolaAgents: `"anthropic/claude-3-5-sonnet-20241022"` (OpenRouter format)

**OpenRouter Priority**: Code prioritizes OpenRouter API when `OPENROUTER_API_KEY` is set. Falls back to Anthropic/OpenAI if not available.

## Important Patterns

### Creating Agno Agents

```python
from agno import Agent, ModelSettings

agent = Agent(
    name="agent_name",
    model=ModelSettings(id="claude-3-5-sonnet-20241022"),
    instructions=system_prompt,
    # Optional: tools, structured_outputs
)
```

### SmolaAgents Manager Pattern

```python
from smolagents import ToolCallingAgent, ManagedAgent

# Create managed agents
managed_agents = [
    ManagedAgent(
        agent=ToolCallingAgent(...),
        name="agent_name",
        description="Agent responsibility"
    )
]

# Create manager
manager = ToolCallingAgent(
    tools=[],
    managed_agents=managed_agents,
    system_prompt="Manager coordination instructions..."
)
```

### Async Batch Execution with Limits

```python
from src.utils.concurrency import ConcurrencyManager

manager = ConcurrencyManager.for_survey()
results = await manager.execute_batch(tasks, max_concurrency=100)
```

## Code Style

- Line length: 120 characters
- Python 3.10+ required
- Use async/await for I/O operations
- Type hints preferred (but not strictly enforced)
- Pydantic for all data models
- Structured logging with logger.info/warning/error

## API Endpoints

- `GET /`: Project information
- `GET /health`: Health check (used by Render.com)
- `GET /config`: Current configuration (non-sensitive)
- `GET /docs`: Swagger UI
- `GET /redoc`: ReDoc documentation

Future endpoints (not yet implemented):
- `POST /api/surveys`: Create survey deployment
- `POST /api/focus-groups`: Create focus group session
- `POST /api/audiences`: Generate audience personas
- `GET /api/insights`: Extract research insights
