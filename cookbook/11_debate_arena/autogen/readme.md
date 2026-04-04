# Debate Arena — AutoGen Edition

Implements the same `debate.spl` pattern using AutoGen:
Two `ConversableAgent` instances (`Pro` and `Con`) conduct a round-robin chat,
followed by a `Judge` agent that evaluates the final transcript.

## Setup

```bash
pip install pyautogen
```

Requires Ollama running locally:
```bash
ollama serve
ollama pull gemma3   # or any model you prefer
```

## Run

```bash
# From SPL20/ root
python cookbook/11_debate_arena/autogen/debate_autogen.py --topic "AI should be open-sourced"
```

## Validate

Expected console output pattern:
```
Pro (to Con):
Debate motion: AI should be open-sourced. Please start with your opening statement.
--------------------------------------------------------------------------------
Con (to Pro):
<opening statement>
...
Judge deliberating ...

============================================================
VERDICT:
<judge verdict text>
```

Check log files written to `cookbook/11_debate_arena/autogen/logs-autogen`:
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
| `debate_autogen.py` | ~110 |

Extra lines in AutoGen come from: agent initialization, explicit system messages,
manual looping/turn management within `initiate_chat`, and the final explicit
invocation of the `Judge` agent. SPL's `WORKFLOW` and `GENERATE` syntax allow
for more compact orchestration of these same steps.
