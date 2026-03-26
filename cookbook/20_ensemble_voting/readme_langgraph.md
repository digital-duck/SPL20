# Recipe 20 v2: Ensemble Voting — LangGraph vs SPL

This file documents `ensemble_langgraph.py`, a faithful LangGraph re-implementation
of `ensemble_v2.spl`, written purely to benchmark expressiveness and conciseness.

**Both implementations are functionally identical** — same pipeline, same defaults,
same log files, same deterministic winner selection.

---

## Side-by-side comparison

| Dimension | `ensemble_v2.spl` | `ensemble_langgraph.py` |
|---|---|---|
| **Non-comment lines** | **107** | **213** |
| **Total lines** | 220 | 294 |
| **State management** | implicit `@variables` | explicit `TypedDict` with 14 fields |
| **Looping** | `WHILE @i < @n_candidates DO` | conditional edge + routing function |
| **Model dispatch** | `GENERATE ... USING MODEL @model` | `ChatOllama(model=...).invoke(...)` |
| **File logging** | `CALL write_file(...)` built-in | custom `_write()` helper function |
| **CLI** | `spl run ... question="..."` | 10-line `argparse` block |
| **Graph wiring** | read top to bottom | nodes + edges + entry point + compile |
| **Accumulators** | `list_append()` built-in | pre-initialise all lists as `[]` in state |
| **Prompt definitions** | `CREATE FUNCTION ... AS $$ ... $$` | module-level string constants |
| **Error handling** | `EXCEPTION WHEN BudgetExceeded` | not shown (requires custom exception wrapping) |
| **Dependencies** | `spl` CLI | `langgraph`, `langchain-ollama`, `argparse` |

### What this tells us about SPL

The LangGraph version is idiomatic Python — no shortcuts taken.
The 2× line count difference comes from things SPL eliminates entirely:

- **No state declaration** — `@candidates`, `@scores`, `@i` just exist
- **No graph wiring** — sequential code *is* the graph
- **No loop machinery** — `WHILE` is a statement, not a conditional routing edge
- **No boilerplate CLI** — `INPUT:` block *is* the argument parser
- **No model plumbing** — `USING MODEL` is a keyword, not an SDK call

---

## Architecture (shared by both implementations)

```
@models pool
     │
     ├─ pick_model()  ──────────────────► GENERATE answer_candidate   USING MODEL @gen_model
     │                                            │
     └─ pick_model(exclude=@gen_model) ──► GENERATE score_candidate   USING MODEL @score_model
                                                  │
                                         (loop N times)
                                                  │
                                         GENERATE find_consensus       USING MODEL @consensus_model
                                                  │
                                         CALL select_winner()          ← deterministic argmax, 0 tokens
                                                  │
                                         GENERATE polish()             USING MODEL @polish_model
```

---

## Prerequisites

```bash
pip install langgraph langchain-ollama
```

Ollama must be running with at least one model pulled:

```bash
ollama pull llama3.2
ollama pull qwen2.5
ollama pull gemma3
ollama pull mistral
ollama pull deepseek-r1
```

---

## Usage

```bash
# Minimal — uses all defaults (random mode, 5 candidates)
python cookbook/20_ensemble_voting/ensemble_langgraph.py \
    --question "What causes inflation?"

# Custom pool, more candidates
python cookbook/20_ensemble_voting/ensemble_langgraph.py \
    --question "Is Rust faster than C++?" \
    --models llama3.2 qwen2.5 gemma3 mistral \
    --n-candidates 7 \
    --polish-model deepseek-r1

# Positional / reproducible mode
python cookbook/20_ensemble_voting/ensemble_langgraph.py \
    --question "What is the best database for time-series data?" \
    --random-selection false
```

## Equivalent SPL command

```bash
spl run cookbook/20_ensemble_voting/ensemble_v2.spl \
    --adapter ollama \
    --tools cookbook/20_ensemble_voting/tools.py \
    question="What causes inflation?"
```

---

## Parameters

| Flag | Default | Description |
|---|---|---|
| `--question` | *(required)* | The question to answer |
| `--models` | `llama3.2 qwen2.5 gemma3 mistral deepseek-r1` | Pool of models to draw from |
| `--n-candidates` | `5` | Number of candidate answers |
| `--random-selection` | `true` | `true` = random draw; `false` = positional rotation |
| `--consensus-model` | `qwen2.5` | Model for the consensus step |
| `--polish-model` | `deepseek-r1` | Model for the final polish pass |
| `--log-dir` | `cookbook/20_ensemble_voting/logs` | Directory for per-step logs |

---

## Log files

Identical to `ensemble_v2.spl` — both write to the same `--log-dir`:

| File | Contents |
|---|---|
| `candidate_N.md` | Raw answer + which model generated it |
| `score_N.md` | Numeric score + generator/scorer model pair |
| `consensus.md` | Consensus summary across all candidates |
| `winner.md` | Winning candidate (pre-polish) |
| `final_answer.md` | Polished final answer |
