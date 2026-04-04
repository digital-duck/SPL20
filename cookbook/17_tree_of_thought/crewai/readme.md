# Tree of Thought — CrewAI Edition

Implements the same `tree_of_thought.spl` pattern using CrewAI:
Multiple `Agent` instances (Researcher, Analyst, Selector, Refiner, Judge)
collaborate on `Task` objects managed by a Python-orchestrated loop to explore
reasoning paths across different models and produce a validated final solution.

## Setup

```bash
pip install crewai langchain-ollama
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
python cookbook/17_tree_of_thought/crewai/tree_of_thought_crewai.py \
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

Check logs in `cookbook/17_tree_of_thought/crewai/logs-crewai`.

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
| `tree_of_thought_crewai.py` | ~150 |

Extra lines in CrewAI come from: detailed agent definitions (role, goal, backstory),
manual Python-based loop and model management, and the overhead of kicking off
individual tasks via `Crew`. SPL's native support for multi-model iteration
(`WHILE` + `USING MODEL`) and structured workflows leads to a more direct and
compact implementation.
