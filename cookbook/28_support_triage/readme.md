# Recipe 28: Customer Support Triage

Classify → route → draft response in one workflow. Detects urgency, escalates critical tickets immediately, and drafts a quality-checked response for everything else.

## Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `ticket` | TEXT | *(required)* | The raw customer support message |
| `product` | TEXT | `our product` | Product name to reference in the response |
| `tone` | TEXT | `professional` | Response tone: `professional`, `empathetic`, `formal`, `friendly` |

## Usage

```bash
spl2 run cookbook/28_support_triage/support_triage.spl --adapter ollama \
    ticket="My account has been charged twice for the same order #12345"

spl2 run cookbook/28_support_triage/support_triage.spl --adapter ollama \
    ticket="I can't log in, password reset email never arrives" \
    product="CloudDash" \
    tone="empathetic"

spl2 run cookbook/28_support_triage/support_triage.spl --adapter ollama \
    ticket="How do I export my data?" \
    tone="friendly"
```

## Categories and routing

| Category | Team | SLA | Priority |
|---|---|---|---|
| `billing` | Finance | 4h | High |
| `account` | Auth | 2h | High |
| `technical` | Engineering | 8h | Medium |
| `complaint` | Customer Success | 1h | Urgent |
| `general` | First-line | 48h | Low |

## Output status

| Status | Meaning |
|---|---|
| `escalated` | Urgency > 8; escalation alert committed |
| `drafted` | Quality check passed |
| `drafted_revised` | Quality was low; one revision applied |
| `fallback` | Generation error; fallback response used |
