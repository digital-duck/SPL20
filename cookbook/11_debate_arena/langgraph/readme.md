# Debate Arena — LangGraph Edition

Implements the same `debate.spl` pattern using LangGraph:
a state graph with five nodes (`pro_opening → con_opening → pro_rebuttal → con_rebuttal → judge`)
and conditional edges to manage the round-robin rebuttal loop.

## Setup

```bash
pip install langgraph langchain-ollama
```

Requires Ollama running locally:
```bash
ollama serve
ollama pull gemma3   # or any model you prefer
```

## Run

```bash
# From SPL20/ root
python cookbook/11_debate_arena/langgraph/debate_langgraph.py --topic "AI should be open-sourced"
```

## Validate

Expected console output pattern:
```
[0] Pro opening ...
[0] Con opening ...
[0] Pro rebuttal ...
[0] Con rebuttal ...
[1] Pro rebuttal ...
[1] Con rebuttal ...
...
Judge deliberating ...

============================================================
VERDICT:
<judge verdict text>
```

Check log files written to `cookbook/11_debate_arena/langgraph/logs-langgraph`:
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
| `debate_langgraph.py` | ~130 |

Extra lines in LangGraph come from: explicit `TypedDict` state, node function overhead,
manual history concatenation (`state["pro_history"] + "\n---\n" + arg`), and graph wiring.
SPL handles the state updates and sequential/looping flow more concisely with its procedural syntax.
