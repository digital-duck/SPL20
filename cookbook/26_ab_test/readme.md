# Recipe 26 — Prompt A/B Test

Compare two prompt variants using CTEs + `EVALUATE` scoring. The workflow picks the winner automatically.

## Key Feature

CTEs run both variants, `GENERATE` scores each against a rubric, and `EVALUATE` selects the winner — all within a single `.spl` workflow. No external harness needed.

## Usage

```bash
# Compare explanation styles
spl2 run cookbook/26_ab_test/ab_test.spl --adapter ollama -m gemma3 \
    task="Explain neural networks" \
    prompt_a="Explain like I'm 5" \
    prompt_b="Give a technical explanation with analogies"

# Compare marketing angles
spl2 run cookbook/26_ab_test/ab_test.spl --adapter ollama \
    task="Write a product description for a standing desk" \
    prompt_a="Focus on health benefits" \
    prompt_b="Focus on productivity and focus"

# Tighter tie threshold (must differ by 2+ points to declare a winner)
spl2 run cookbook/26_ab_test/ab_test.spl --adapter ollama \
    task="Summarize the French Revolution in 3 sentences" \
    prompt_a="Be concise and factual" \
    prompt_b="Be vivid and narrative" \
    winner_threshold=2.0
```

## Output

```
Winner: B (score 7.8 vs 6.2, margin 1.6)

[Variant B response here...]

Rationale: Variant B scored higher on engagement (9 vs 6) while maintaining equal clarity.
```

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `task` | required | The task both variants respond to |
| `prompt_a` | required | First prompt style or instruction |
| `prompt_b` | required | Second prompt style or instruction |
| `winner_threshold` | `1.5` | Minimum score difference to declare a winner (below = tie) |
