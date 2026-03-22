# Recipe 18: Guardrails Pipeline

Safety-first generation: keyword pre-screen → LLM input classification → PII detection/redaction → safe generation → output validation. Four gates before a response is committed.

## What's in this recipe

| File | Purpose |
|---|---|
| `guardrails.spl` | Main SPL workflow |
| `tools.py` | Python tools: `load_test_input`, `list_test_inputs`, `detect_pii`, `redact_pii`, `classify_input_keywords` |
| `test_inputs.json` | 17 pre-built test inputs across safe, PII, harmful, off-topic, and edge categories |

## Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `input_id` | TEXT | `''` | Test input ID from catalog (e.g. `safe_encryption`, `pii_ssn`, `harmful_malware`) |
| `user_input` | TEXT | `''` | Raw input for ad-hoc runs (used when `input_id` is blank) |

Pass `input_id` for catalog-grounded testing (recommended).
Pass `user_input` alone for ad-hoc runs with no catalog.

## Usage

Always pass `--tools tools.py`:

```bash
# From catalog — safe input
spl run cookbook/18_guardrails/guardrails.spl \
    --adapter ollama -m gemma3 \
    --tools cookbook/18_guardrails/tools.py \
    input_id=safe_encryption \
    2>&1 | tee cookbook/out/18_guardrails-$(date +%Y%m%d_%H%M%S).md

# From catalog — PII redaction test
spl run cookbook/18_guardrails/guardrails.spl \
    --adapter ollama -m gemma3 \
    --tools cookbook/18_guardrails/tools.py \
    input_id=pii_ssn

# From catalog — harmful request (should block at Gate 1)
spl run cookbook/18_guardrails/guardrails.spl \
    --adapter ollama -m gemma3 \
    --tools cookbook/18_guardrails/tools.py \
    input_id=harmful_malware

# From catalog — multiple PII types
spl run cookbook/18_guardrails/guardrails.spl \
    --adapter ollama -m gemma3 \
    --tools cookbook/18_guardrails/tools.py \
    input_id=pii_multiple

# Ad-hoc — no catalog needed
spl run cookbook/18_guardrails/guardrails.spl \
    --adapter ollama -m gemma3 \
    --tools cookbook/18_guardrails/tools.py \
    user_input="Explain how encryption works"

# Discover available test inputs
spl run ... input_id=list
```

## Workflow steps

```
user_input  (or loaded from catalog via input_id)
    │
    ├─ CALL load_test_input()              ← catalog context — zero LLM cost
    │
    ├─ Gate 1a: CALL classify_input_keywords()  ← regex keyword pre-screen — zero LLM cost
    │       WHEN harmful   → COMMIT blocked_harmful
    │       WHEN off_topic → COMMIT blocked_off_topic
    │
    ├─ Gate 1b: GENERATE classify_input()       ← LLM for nuanced classification
    │       WHEN harmful   → COMMIT blocked_harmful
    │       WHEN off_topic → COMMIT blocked_off_topic
    │
    ├─ Gate 2: CALL detect_pii()                ← regex detection — zero LLM cost
    │       WHEN pii_found → CALL redact_pii()  ← regex redaction — zero LLM cost
    │
    ├─ Gate 3: GENERATE safe_response()         ← LLM generation on clean input
    │
    └─ Gate 4: GENERATE validate_output()       ← LLM output check
            WHEN safe         → COMMIT complete
            WHEN contains_pii → CALL redact_pii() → COMMIT
            WHEN hallucination→ RETRY temp=0.1
            OTHERWISE         → COMMIT with fallback message
```

## Python tools (`tools.py`)

### `load_test_input(input_id)`
Returns a structured text block with the input text, category, expected class, PII flags, and design notes.
Grounds `classify_input` with test context.

### `list_test_inputs()`
Lists all test input IDs, categories, and notes from `test_inputs.json`.

### `detect_pii(text)`
Regex-based detection for SSN, credit card numbers, email addresses, and phone numbers.
Returns `pii_found:{detail_json}` or `clean`. Replaces `GENERATE detect_pii()` — zero tokens.

### `redact_pii(text)`
Regex-based redaction — replaces each PII type with a labelled placeholder:
`[REDACTED-SSN]`, `[REDACTED-CC]`, `[REDACTED-EMAIL]`, `[REDACTED-PHONE]`.
Replaces `GENERATE redact_pii()` — zero tokens.

### `classify_input_keywords(text)`
Keyword pre-screen against lists of harmful and off-topic terms.
Returns `harmful:keyword=<kw>`, `off_topic:keyword=<kw>`, or `safe`.
Used as Gate 1a before the LLM classifier to avoid wasting tokens on obvious cases.

## Test input catalog (`test_inputs.json`)

| `input_id` | Category | PII | Notes |
|---|---|---|---|
| `safe_encryption` | safe | — | Clean technical question |
| `safe_poem` | safe | — | Creative request |
| `safe_recipe` | safe | — | Everyday helpful request |
| `safe_explain_sql` | safe | — | Technical but harmless |
| `pii_ssn` | pii | SSN | SSN should be redacted |
| `pii_credit_card` | pii | CC | Credit card number |
| `pii_email` | pii | email | Email addresses |
| `pii_phone` | pii | phone | Phone numbers |
| `pii_multiple` | pii | SSN+email+phone | Multiple PII types |
| `harmful_malware` | harmful | — | Blocked at Gate 1 |
| `harmful_violence` | harmful | — | Blocked at Gate 1 |
| `harmful_phishing` | harmful | — | Blocked at Gate 1 |
| `off_topic_stock` | off_topic | — | Financial advice |
| `off_topic_medical` | off_topic | — | Medical diagnosis |
| `edge_pii_in_code` | edge | email | PII in a code snippet |
| `edge_borderline` | edge | — | Educational/historical |
| `edge_empty` | edge | — | Empty input robustness |

## PII patterns detected

| Type | Pattern example |
|---|---|
| SSN | `123-45-6789` |
| Credit card | `4111 1111 1111 1111` or `4111111111111111` |
| Email | `user@example.com` |
| Phone | `(555) 867-5309`, `1-800-555-0100` |

## Output status

| Status | Meaning |
|---|---|
| `complete` | Passed all gates, safe response committed |
| `blocked_harmful` | Input flagged as harmful (keyword or LLM) |
| `blocked_off_topic` | Input outside scope (keyword or LLM) |
| `refused` | Model refused the request |
| `hallucination_blocked` | Output failed hallucination check |
| `budget_limit` | Token budget exceeded |
