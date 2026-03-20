# Recipe 20: Ensemble Voting

Generates 5 independent candidate answers, scores each on accuracy/completeness/clarity, finds consensus across candidates, selects the winner, and polishes it.

## Pattern

```
5 × answer_candidate(question)
  └─► 5 × score_candidate
        └─► find_consensus(all 5)
              └─► select_winner(scores + consensus)
                    └─► polish(winner, consensus) → final_answer
```

## Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `question` | TEXT | *(required)* | The question to answer via ensemble |

## Usage

```bash
spl2 run cookbook/20_ensemble_voting/ensemble.spl --adapter ollama \
    question="What causes inflation?"

spl2 run cookbook/20_ensemble_voting/ensemble.spl --adapter ollama \
    question="Is Rust faster than C++?"

spl2 run cookbook/20_ensemble_voting/ensemble.spl --adapter ollama -m llama3.2 \
    question="What is the best database for time-series data?"
```

## Output status

| Status | Meaning |
|---|---|
| `complete` | All 5 candidates evaluated |
| `partial` | Budget exceeded; top 3 used for voting |
