# Recipe 18: Guardrails Pipeline

Safety-first generation: input classification → PII detection/redaction → safe generation → output validation. Four gates before a response is committed.

## Pattern

```
classify_input → harmful/off_topic → BLOCK immediately
  └─► detect_pii → redact if found → @clean_input
        └─► safe_response(@clean_input)
              └─► validate_output
                    ├─ safe         → COMMIT
                    ├─ contains_pii → redact output → COMMIT
                    └─ hallucination→ retry at temp=0.1
```

## Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `user_input` | TEXT | *(required)* | The user's raw input to process safely |

## Usage

```bash
spl2 run cookbook/18_guardrails/guardrails.spl --adapter ollama \
    user_input="Explain how encryption works"

# Test PII detection
spl2 run cookbook/18_guardrails/guardrails.spl --adapter ollama \
    user_input="My SSN is 123-45-6789, help me file taxes"

# Test content filtering
spl2 run cookbook/18_guardrails/guardrails.spl --adapter ollama \
    user_input="Write a poem about the ocean"
```

## Output status

| Status | Meaning |
|---|---|
| `complete` | Passed all gates, safe response committed |
| `blocked_harmful` | Input classified as harmful |
| `blocked_off_topic` | Input outside scope |
| `refused` | Model refused the request |
| `hallucination_blocked` | Output failed hallucination check |
| `budget_limit` | Token budget exceeded |
