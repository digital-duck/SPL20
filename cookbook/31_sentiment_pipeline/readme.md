# Recipe 31: Sentiment Pipeline

Batch sentiment analysis over a delimited list of items. Classifies each item, computes aggregate statistics, identifies extremes, and produces a trend report.

## Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `items` | TEXT | *(required)* | Delimited list of texts to analyze |
| `delimiter` | TEXT | `\|` | Separator between items |
| `domain` | TEXT | `general` | Domain context (e.g. `product_reviews`, `social_media`, `support_tickets`) |

## Usage

```bash
# Pipe-delimited inline list
spl2 run cookbook/31_sentiment_pipeline/sentiment.spl --adapter ollama \
    items="Great product, love it! | Terrible experience, never again | It was okay I guess" \
    domain="product_reviews"

# From file (newline-delimited)
spl2 run cookbook/31_sentiment_pipeline/sentiment.spl --adapter ollama \
    items="$(cat reviews.txt)" \
    delimiter="\n" \
    domain="product_reviews"
```

## Sentiment schema per item

| Field | Type | Description |
|---|---|---|
| `label` | enum | `positive`, `negative`, `neutral`, `mixed` |
| `score` | float | −1.0 to 1.0 |
| `confidence` | float | 0.0 to 1.0 |
| `emotions` | array | Detected emotion labels |
| `key_phrases` | array | Most significant phrases |

## Output status

| Status | Meaning |
|---|---|
| `complete` | Full report with all items analyzed |
| `stats_only` | Too many items; statistics only returned |
