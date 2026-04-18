# ReAct Agent — LangGraph Edition

Implements the same `react_agent.spl` pattern using LangGraph:
a `StateGraph` with deterministic tool nodes (`search`, `calc`) feeding a
single LLM node (`report`), plus a conditional error path mirroring
SPL's `EXCEPTION WHEN SearchFailed`.

Note: SPL's `CALL` (zero LLM tokens, deterministic) vs `GENERATE` (probabilistic)
is a language-level distinction. LangGraph has no such primitive — all nodes are
Python functions; the programmer must manually track which steps invoke the LLM.

## Setup

```bash
conda create -n langgraph python=3.11 -y
conda activate langgraph
pip install langgraph langchain-ollama
```

Requires Ollama running locally:
```bash
ollama serve
ollama pull gemma3
```

## Run

```bash
# From SPL20/ root
python cookbook/06_react_agent/langgraph/react_langgraph.py \
    --country France --year 2023

python cookbook/06_react_agent/langgraph/react_langgraph.py \
    --country India --year 2023 --model llama3.2 \
    --log-dir cookbook/06_react_agent/langgraph/logs
```

Supported countries: China, France, USA, India, Germany, Brazil

## Validate

Expected console output pattern:
```
Fetching population | France 2022-2023 ...
Computing growth rate ...
Generating report ...
Committed | status=complete
============================================================
<2-3 sentence population growth report>
```

## SPL equivalent

```bash
spl run cookbook/06_react_agent/react_agent.spl \
    --adapter claude_cli --model claude-sonnet-4-6 \
    --allowed-tools WebSearch \
    --tools cookbook/06_react_agent/tools.py \
    country="France"
```

## LOC comparison

| File | LOC (non-blank, non-comment) |
|------|------------------------------|
| `react_agent.spl` | 43 |
| `react_langgraph.py` | 85 |

Extra lines come from: explicit `TypedDict` state, 5 node functions, graph wiring,
conditional routing function for EXCEPTION, and `argparse` boilerplate. The
CALL/GENERATE distinction — free in SPL — requires manual discipline in LangGraph.
