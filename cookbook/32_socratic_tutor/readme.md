# Recipe 32: Socratic Tutor

Guides a student to discover answers through questions rather than direct instruction. Simulates a 3-question dialogue, assesses understanding, and adapts the final question accordingly.

## Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `topic` | TEXT | *(required)* | The concept or question to explore |
| `student_level` | TEXT | `high school` | Audience level (e.g. `middle school`, `high school`, `undergraduate`, `expert`) |
| `max_questions` | INT | `5` | Maximum questions in the dialogue |

## Usage

```bash
spl2 run cookbook/32_socratic_tutor/socratic_tutor.spl --adapter ollama \
    topic="Why does the sky appear blue?" \
    student_level="middle school"

spl2 run cookbook/32_socratic_tutor/socratic_tutor.spl --adapter ollama \
    topic="Prove that sqrt(2) is irrational" \
    student_level="undergraduate" \
    max_questions=5

spl2 run cookbook/32_socratic_tutor/socratic_tutor.spl --adapter ollama -m llama3.2 \
    topic="What is recursion?" \
    student_level="high school"
```

## Notes

- The tutor persona never gives direct answers — all outputs are guiding questions.
- A simulated student response is generated to model a typical learner at the given level.
- If understanding score > 7, the tutor moves to a consolidation question; otherwise it provides a hint question.
