# Chain of Thought — AutoGen Edition

Implements the same `chain.spl` pattern using AutoGen:
three `ConversableAgent` instances (Researcher, Analyst, Summarizer) driven
sequentially by a proxy agent via `initiate_chat(max_turns=1)`.
AutoGen's conversation model is designed for back-and-forth exchange —
a pure sequential pipeline requires explicit per-step `initiate_chat` calls.

## Setup

```bash
conda create -n autogen python=3.11 -y
conda activate autogen
pip install pyautogen
```

Requires Ollama running locally with OpenAI-compatible endpoint:
```bash
ollama serve
ollama pull gemma3   # or any model you prefer
```

> AutoGen uses the OpenAI-compatible endpoint Ollama exposes at
> `http://localhost:11434/v1` — no API key needed (uses `"ollama"` as placeholder).

## Run

```bash
# From SPL20/ root
python cookbook/09_chain_of_thought/autogen/chain_autogen.py \
    --topic "distributed AI inference"

# Custom model
python cookbook/09_chain_of_thought/autogen/chain_autogen.py \
    --topic "quantum computing" \
    --model llama3.2 \
    --log-dir cookbook/09_chain_of_thought/autogen/logs
```

## Validate

Expected console output pattern:
```
Step 1 | researching ...
Step 2 | analyzing ...
Step 3 | summarizing ...
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
    --adapter ollama -m gemma3 \
    topic="distributed AI inference"
```

## LOC comparison

| File | LOC (non-blank, non-comment) |
|------|------------------------------|
| `chain.spl` | 14 |
| `chain_autogen.py` | 62 |

Extra lines come from: three Agent instantiations, three `initiate_chat` calls with
result extraction, `llm_config` wiring, and `argparse` boilerplate. AutoGen's
`max_turns=1` pattern works for sequential pipelines but is not a first-class
language construct — each step requires explicit agent setup.
