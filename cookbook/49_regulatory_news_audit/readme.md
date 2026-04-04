
recipe suggested by Qwen 3.6 Plus

```bash
spl run cookbook/49_regulatory_news_audit/audit_news.spl \
  --adapter ollama -m qwen3 \
  news_batch="$(cat cookbook/49_regulatory_news_audit/data/news_feed.txt)" \
  --tools cookbook/tools/finance_helpers.py
```

