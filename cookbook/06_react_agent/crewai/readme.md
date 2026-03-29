# ReAct Agent — CrewAI Edition

Implements the same `react_agent.spl` pattern using CrewAI:
`@tool` decorators wrap deterministic functions; a single LLM `Agent`
calls those tools and generates the final report via its ReAct loop.
CrewAI has no explicit EXCEPTION primitive — error handling falls to
the agent's task description.

Note: SPL's `CALL` (zero LLM tokens, deterministic) vs `GENERATE` (probabilistic)
is a language-level distinction. CrewAI has no such primitive — both tool calls
and LLM reasoning are handled by the same Agent.

## Setup

```bash
conda create -n crewai python=3.11 -y
conda activate crewai
pip install crewai langchain-ollama
```

Requires Ollama running locally:
```bash
ollama serve
ollama pull gemma3
```

## Run

```bash
# From SPL20/ root
python cookbook/06_react_agent/crewai/react_crewai.py \
    --country France --year 2023

python cookbook/06_react_agent/crewai/react_crewai.py \
    --country India --year 2023 --model llama3.2 \
    --log-dir cookbook/06_react_agent/crewai/logs
```

Supported countries: China, France, USA, India, Germany, Brazil

## Validate

Expected console output pattern:
```
Running population growth analysis | France 2022-2023 ...
Committed | status=complete
============================================================
<2-3 sentence population growth report>
```

## SPL equivalent

```bash
spl run cookbook/06_react_agent/react_agent.spl \
    --adapter claude_cli -m claude-sonnet-4-6 \
    --allowed-tools WebSearch \
    --tools cookbook/06_react_agent/tools.py \
    country="France"
```

## LOC comparison

| File | LOC (non-blank, non-comment) |
|------|------------------------------|
| `react_agent.spl` | 43 |
| `react_crewai.py` | 100 |

Extra lines come from: `@tool` decorator definitions (docstrings required by
CrewAI for tool discovery), `Agent`/`Task`/`Crew` object construction,
and `argparse` boilerplate. The CALL/GENERATE distinction — free in SPL —
is invisible in CrewAI; the agent's ReAct loop conflates deterministic
tool calls with probabilistic reasoning steps.
