# ReAct Agent — AutoGen Edition

Implements the same `react_agent.spl` pattern using AutoGen:
deterministic tool calls (plain Python functions) + single LLM `ConversableAgent`
for the final report, plus a `try/except` error path mirroring
SPL's `EXCEPTION WHEN SearchFailed`.

Note: SPL's `CALL` (zero LLM tokens, deterministic) vs `GENERATE` (probabilistic)
is a language-level distinction. AutoGen has no such primitive — all functions are
plain Python; the programmer must manually track which steps invoke the LLM.

## Setup

```bash
conda create -n autogen python=3.11 -y
conda activate autogen
pip install pyautogen
```

Requires Ollama running locally:
```bash
ollama serve
ollama pull gemma3
```

## Run

```bash
# From SPL20/ root
python cookbook/06_react_agent/autogen/react_autogen.py \
    --country France --year 2023

python cookbook/06_react_agent/autogen/react_autogen.py \
    --country India --year 2023 --model llama3.2 \
    --log-dir cookbook/06_react_agent/autogen/logs
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
| `react_autogen.py` | 93 |

Extra lines come from: explicit `try/except` for EXCEPTION handling, two
`ConversableAgent` instantiations (proxy + reporter), `initiate_chat` wiring,
and `argparse` boilerplate. The CALL/GENERATE distinction — free in SPL —
requires manual discipline in AutoGen.
