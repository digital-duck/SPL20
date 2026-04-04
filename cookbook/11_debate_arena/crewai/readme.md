# Debate Arena — CrewAI Edition

Implements the same `debate.spl` pattern using CrewAI:
Three `Agent` instances (`Proponent`, `Opponent`, `Judge`) collaborate on a series
of `Task` objects to simulate a structured debate and final verdict.

## Setup

```bash
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
python cookbook/11_debate_arena/crewai/debate_crewai.py --topic "AI should be open-sourced"
```

## Validate

Expected console output pattern:
```
[0] Pro opening ...
[0] Con opening ...
[0] Pro rebuttal ...
[0] Con rebuttal ...
...
Judge deliberating ...

============================================================
VERDICT:
<judge verdict text>
```

Check log files written to `cookbook/11_debate_arena/crewai/logs-crewai`:
```
opening_pro.md
opening_con.md
round_0_pro.md
round_0_con.md
...
verdict.md
```

## SPL equivalent

```bash
spl run cookbook/11_debate_arena/debate.spl \
    --adapter ollama -m gemma3 \
    topic="AI should be open-sourced"
```

## LOC comparison

| File | LOC (non-blank, non-comment) |
|------|------------------------------|
| `debate.spl` | ~60 |
| `debate_crewai.py` | ~120 |

Extra lines in CrewAI come from: agent and task definitions (role, goal, backstory),
explicit loop management in Python (since CrewAI lacks native looping syntax),
and the boilerplate for kicking off each individual task through a `Crew`.
SPL's procedural control flow allows for more direct expression of the debate loop.
