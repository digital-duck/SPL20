# Recipe 33: Interview Simulator

Two-persona structured Q&A: an interviewer asks targeted questions, a candidate answers, and an evaluator scores each response on accuracy, depth, communication, and practical experience.

## Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `role` | TEXT | *(required)* | Job role being interviewed for |
| `focus` | TEXT | *(required)* | Interview focus area (e.g. `system design`, `machine learning`) |
| `difficulty` | TEXT | `medium` | Question difficulty: `easy`, `medium`, `hard` |
| `num_questions` | INT | `3` | Number of interview questions |
| `experience` | TEXT | `5 years` | Candidate's experience level |

## Usage

```bash
spl2 run cookbook/33_interview_sim/interview_sim.spl --adapter ollama \
    role="Senior Software Engineer" \
    focus="system design"

spl2 run cookbook/33_interview_sim/interview_sim.spl --adapter ollama \
    role="Data Scientist" \
    focus="machine learning" \
    num_questions=4 \
    difficulty="hard"

spl2 run cookbook/33_interview_sim/interview_sim.spl --adapter ollama -m llama3.2 \
    role="DevOps Engineer" \
    focus="Kubernetes" \
    experience="3 years"
```

## Evaluation rubric (per question)

| Dimension | Scale | Description |
|---|---|---|
| Technical accuracy | 0–10 | Is the answer correct? |
| Depth | 0–10 | Beyond surface level? |
| Communication | 0–10 | Clear and well-structured? |
| Practical experience | 0–10 | References real scenarios? |
