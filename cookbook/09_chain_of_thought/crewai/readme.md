# Chain of Thought — CrewAI Edition

Implements the same `chain.spl` pattern using CrewAI:
three `Agent` instances (Researcher, Analyst, Summarizer) with sequential
`Task` objects wired via `context=` to pass outputs downstream.
`Process.sequential` handles execution order.

## Setup

```bash
conda create -n crewai python=3.11 -y
conda activate crewai
pip install crewai langchain-ollama
```

Requires Ollama running locally:
```bash
ollama serve
ollama pull gemma3   # or any model you prefer
```

## Run

```bash
# From SPL20/ root
python cookbook/09_chain_of_thought/crewai/chain_crewai.py \
    --topic "distributed AI inference"

# Custom model
python cookbook/09_chain_of_thought/crewai/chain_crewai.py \
    --topic "quantum computing" \
    --model llama3.2 \
    --log-dir cookbook/09_chain_of_thought/crewai/logs
```

## Validate

Expected console output pattern:
```
Running chain of thought pipeline ...
Done | status=complete
============================================================
<final summary text>
```

Check log files written to `--log-dir`:
```
logs/research.md   ← Step 1 output
logs/analysis.md   ← Step 2 output
logs/summary.md    ← Step 3 output
logs/final.md      ← committed output
```

## SPL equivalent

```bash
spl run cookbook/09_chain_of_thought/chain.spl \
    --adapter ollama --model gemma3 \
    topic="distributed AI inference"
```

## LOC comparison

| File | LOC (non-blank, non-comment) |
|------|------------------------------|
| `chain.spl` | 14 |
| `chain_crewai.py` | 58 |

Extra lines come from: Agent/Task/Crew object construction (role, goal, backstory
required per agent), explicit `context=` wiring between tasks, and `argparse`
boilerplate. CrewAI's `Process.sequential` is the closest native equivalent to
SPL's implicit sequential WORKFLOW — but requires 3 object definitions where SPL
uses 3 lines.
