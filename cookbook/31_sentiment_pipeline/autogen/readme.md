# Sentiment Pipeline — AutoGen Edition

Implements the same `sentiment.spl` pattern using AutoGen:
Multiple specialized agents (Analyst, Summarizer, Assembler) are coordinated
by a Python script alongside deterministic tools for loading, splitting, and
statistical aggregation to implement a batch sentiment analysis pipeline.

## Setup

```bash
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
python cookbook/31_sentiment_pipeline/autogen/sentiment_autogen.py \
    --items "Great product, love it! | Terrible experience, never again | It was okay" \
    --delimiter "|"
```

## Validate

Expected console output pattern:
```
Loading and splitting items ...
Running batch sentiment for 3 items ...
Computing stats and extremes ...
Generating trend narrative ...
Assembling full report ...

============================================================
# Sentiment Analysis Report
...
```

Check logs in `cookbook/31_sentiment_pipeline/autogen/logs-autogen`.

## SPL equivalent

```bash
spl run cookbook/31_sentiment_pipeline/sentiment.spl \
    --adapter ollama --model gemma3 \
    --tools cookbook/31_sentiment_pipeline/tools.py \
    items="Great product, love it! | Terrible experience, never again | It was okay" \
    delimiter="|"
```

## LOC comparison

| File | LOC (non-blank, non-comment) |
|------|------------------------------|
| `sentiment.spl` | ~75 |
| `sentiment_autogen.py` | ~130 |

Extra lines in AutoGen come from: agent definitions with explicit system messages,
manual coordination of the procedural steps, and the implementation of deterministic
tools (file loading, stats, extremes). SPL's native `CALL` and `GENERATE`
constructs with integrated schema support provide a more compact and readable
way to express this data-aggregation pipeline.
