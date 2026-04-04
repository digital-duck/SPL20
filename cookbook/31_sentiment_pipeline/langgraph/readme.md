# Sentiment Pipeline — LangGraph Edition

Implements the same `sentiment.spl` pattern using LangGraph:
a state graph that loads items, runs batch sentiment analysis with structured
output, computes aggregate statistics and identifying extreme cases, and finally
generates a trend narrative and comprehensive report.

## Setup

```bash
pip install langgraph langchain-ollama
```

Requires Ollama running locally:
```bash
ollama serve
ollama pull gemma3
```

## Run

```bash
# From SPL20/ root
python cookbook/31_sentiment_pipeline/langgraph/sentiment_langgraph.py \
    --items "Great product, love it! | Terrible experience, never again | It was okay" \
    --delimiter "|"
```

## Validate

Expected console output pattern:
```
Loading and splitting items ...
Running batch sentiment for 3 items ...
Computing aggregate statistics ...
Identifying extreme cases ...
Generating trend narrative ...
Assembling full report ...

============================================================
FINAL REPORT:
# Sentiment Analysis Report
...
```

Check logs in `cookbook/31_sentiment_pipeline/langgraph/logs-langgraph`.

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
| `sentiment_langgraph.py` | ~200 |

Extra lines in LangGraph come from: state definition, node functions, manual integration
of the tool logic (file loading, stats calculation, extreme detection), and graph
wiring. SPL's native `CALL` and `GENERATE` constructs with integrated schema
support allow for a much more direct and compact implementation of this pipeline.
