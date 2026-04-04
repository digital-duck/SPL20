
recipe suggested by Qwen 3.6 Plus

```bash
spl run cookbook/48_credit_risk/assess_credit_risk.spl \
  --adapter ollama -m qwen3 \
  applicant_data="$(cat cookbook/48_credit_risk/data/applicant_680.json)" \
  credit_score=680 \
  --tools cookbook/tools/finance_helpers.py
```