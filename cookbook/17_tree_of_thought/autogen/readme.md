# Tree of Thought — AutoGen Edition

Implements the same `tree_of_thought.spl` pattern using AutoGen:
Multiple agents (Thinker, Scorer, Selector, Verifier, Synthesizer) are coordinated
by a Python script to explore reasoning paths across different models and
produce a validated final solution.

## Setup

```bash
pip install pyautogen
```

Requires Ollama running locally:
```bash
ollama serve
ollama pull gemma3
ollama pull phi4
ollama pull qwen2.5
```

## Run

```bash
# From SPL20/ root
python cookbook/17_tree_of_thought/autogen/tree_of_thought_autogen.py \
    --problem "How can we reduce microplastic pollution in oceans?"
```

## Validate

Expected console output pattern:
```
Exploring path 1/3 using gemma3...
Exploring path 2/3 using phi4...
Exploring path 3/3 using qwen2.5...
Selecting best path...
Refining winning path...
Verifying solution...
============================================================
FINAL SOLUTION:
<solution text>
```

Check logs in `cookbook/17_tree_of_thought/autogen/logs-autogen`.

## SPL equivalent

```bash
spl run cookbook/17_tree_of_thought/tree_of_thought.spl \
    --adapter ollama \
    problem="How can we reduce microplastic pollution in oceans?"
```

## LOC comparison

| File | LOC (non-blank, non-comment) |
|------|------------------------------|
| `tree_of_thought.spl` | ~65 |
| `tree_of_thought_autogen.py` | ~140 |

Extra lines in AutoGen come from: detailed agent definitions, manual turn-by-turn
coordination of multiple agents and models, and explicit file logging. SPL's
procedural syntax and `USING MODEL` support allow for much more compact
multi-agent orchestration.
