# Sentiment Pipeline — CrewAI Edition

Implements the same `sentiment.spl` pattern using CrewAI:
Multiple `Agent` instances (Sentiment Analyst, Trend Specialist, Report Writer)
collaborate on `Task` objects managed by a Python-orchestrated flow to implement
a batch sentiment analysis pipeline with statistical aggregation.

## Setup

```bash
pip install crewai langchain-ollama
```

Requires Ollama running locally:
```bash
ollama serve
ollama pull gemma3
```

## Run

```bash
# From SPL20/ root
python cookbook/31_sentiment_pipeline/crewai/sentiment_crewai.py \
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

Check logs in `cookbook/31_sentiment_pipeline/crewai/logs-crewai`.

## SPL equivalent

```bash
spl run cookbook/31_sentiment_pipeline/sentiment.spl \
    --adapter ollama -m gemma3 \
    --tools cookbook/31_sentiment_pipeline/tools.py \
    items="Great product, love it! | Terrible experience, never again | It was okay" \
    delimiter="|"
```

## LOC comparison

| File | LOC (non-blank, non-comment) |
|------|------------------------------|
| `sentiment.spl` | ~75 |
| `sentiment_crewai.py` | ~160 |

Extra lines in CrewAI come from: detailed agent and task definitions (role, goal, backstory),
manual Python-based tool coordination (loading, stats, extremes), and the overhead of
kicking off tasks via `Crew`. SPL's native `CALL` and `GENERATE` constructs with
integrated schema support allow for a much more direct and cohesive way to express
this data-aggregation pipeline.
