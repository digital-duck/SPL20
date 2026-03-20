# Recipe 29: Meeting Notes → Action Items

Transcript in, structured output. Normalizes the transcript, extracts action items with owners and priorities, validates for unowned high-priority items, and formats as JSON, Markdown, or email.

## Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `transcript` | TEXT | *(required)* | Meeting transcript text |
| `output_format` | TEXT | `json` | Output format: `json`, `markdown`, or `email` |

## Usage

```bash
# Inline transcript
spl2 run cookbook/29_meeting_actions/meeting_actions.spl --adapter ollama \
    transcript="Alice: we need to fix the login bug before Friday. Bob: I'll handle it. Alice: also need to update the docs" \
    output_format="markdown"

# From file
spl2 run cookbook/29_meeting_actions/meeting_actions.spl --adapter ollama \
    transcript="$(cat meeting.txt)" \
    output_format="json"

# Email format
spl2 run cookbook/29_meeting_actions/meeting_actions.spl --adapter ollama \
    transcript="$(cat standup.txt)" \
    output_format="email"
```

## Output fields (JSON format)

| Field | Description |
|---|---|
| `meeting_summary` | One-paragraph summary |
| `decisions` | List of decisions made |
| `action_items` | List of tasks with owner, due_date, priority |
| `open_questions` | Unresolved questions |
| `next_meeting` | Next meeting reference if mentioned |
