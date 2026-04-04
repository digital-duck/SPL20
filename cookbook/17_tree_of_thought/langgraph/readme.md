# Tree of Thought — LangGraph Edition

Implements the same `tree_of_thought.spl` pattern using LangGraph:
a state graph that explores multiple reasoning paths in parallel (using multiple models),
scores them, selects the best one for refinement and verification, and optionally
synthesizes all paths if the winning solution is found unsound.

## Setup

```bash
pip install langgraph langchain-ollama
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
python cookbook/17_tree_of_thought/langgraph/tree_of_thought_langgraph.py \
    --problem "How can we reduce microplastic pollution in oceans?"
```

## Validate

Expected console output pattern:
```
Exploring path 1/3 using gemma3...
Exploring path 2/3 using phi4...
Exploring path 3/3 using qwen2.5...
Selecting best path ...
Refining winning path ...
Verifying solution ...
============================================================
FINAL SOLUTION:
<solution text>
```

Check logs in `cookbook/17_tree_of_thought/langgraph/logs-langgraph`.

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
| `tree_of_thought_langgraph.py` | ~160 |

Extra lines in LangGraph come from: state definition, node functions, manual model-based
loop management, and graph wiring. SPL's `WHILE` loop combined with `USING MODEL`
syntax makes it significantly more compact for multi-model exploration.
