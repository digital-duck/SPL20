"""
LangGraph equivalent of cookbook/20_ensemble_voting/ensemble_v2.spl

Implements the same ensemble voting pipeline:
  pick_model → generate_candidate → score_candidate (different model)
                                  ↕  loop N times
                     find_consensus → select_winner (argmax) → polish

Usage:
    pip install langgraph langchain-ollama

    python cookbook/20_ensemble_voting/ensemble_langgraph.py \\
        --question "What causes inflation?"

    python cookbook/20_ensemble_voting/ensemble_langgraph.py \\
        --question "Is Rust faster than C++?" \\
        --models llama3.2 qwen2.5 gemma3 mistral deepseek-r1 \\
        --n-candidates 7 \\
        --polish-model deepseek-r1

    # Positional / reproducible mode
    python cookbook/20_ensemble_voting/ensemble_langgraph.py \\
        --question "What is the best database for time-series data?" \\
        --random-selection false
"""

import argparse
import random
import re
from pathlib import Path
from typing import TypedDict

from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph


# ─── Prompts  (mirrors CREATE FUNCTION blocks in ensemble_v2.spl) ─────────────

ANSWER_CANDIDATE = """\
You are an expert assistant. Answer the following question thoroughly and accurately.
Be specific, well-structured, and avoid vague generalities.

Question: {question}"""

SCORE_CANDIDATE = """\
You are a strict evaluator. Score the following answer on three dimensions:
  - Accuracy (0–10): factual correctness
  - Completeness (0–10): covers all key aspects
  - Clarity (0–10): clear and well-structured

Question: {question}

Answer:
{answer}

Return ONLY a single decimal number between 0.0 and 10.0 — the average of the three scores.
No explanation, no label, just the number."""

FIND_CONSENSUS = """\
You are a synthesis expert. Read the following independent answers to the same question,
separated by "---".

{candidates}

Identify:
1. Points agreed on by most answers
2. Points unique to only one answer (notable divergence)
3. Any factual contradictions

Output a concise consensus summary (bullet points)."""

POLISH = """\
You are a world-class editor. Refine the answer below, incorporating the consensus insights.
The result should be authoritative, clear, and complete — the definitive answer to the question.

Question: {question}

Best candidate answer:
{best_answer}

Consensus insights from all candidates:
{consensus}

Write the polished final answer now."""


# ─── State  (SPL manages this implicitly via @ variables) ─────────────────────

class EnsembleState(TypedDict):
    # ── inputs ────────────────────────────────────────────────────────────────
    question:         str
    models:           list[str]
    n_candidates:     int
    random_selection: bool
    consensus_model:  str
    polish_model:     str
    log_dir:          str
    # ── accumulated per iteration ─────────────────────────────────────────────
    candidates:       list[str]
    scores:           list[str]
    gen_models:       list[str]   # which model generated each candidate
    score_models:     list[str]   # which model scored each candidate
    current_index:    int         # loop counter  (SPL: @i)
    # ── pipeline outputs ──────────────────────────────────────────────────────
    consensus:        str
    best_candidate:   str
    final_answer:     str


# ─── Helpers  (in SPL these are either built-ins or tools.py) ─────────────────

def _pick_model(
    models: list[str],
    exclude: str = "",
    random_selection: bool = True,
    index: int = 0,
) -> str:
    """Mirror of tools.py:pick_model."""
    if not models:
        return "gemma3"
    if random_selection:
        filtered = [m for m in models if m != exclude]
        return random.choice(filtered or models)
    n = len(models)
    idx = index % n
    if models[idx] == exclude:
        idx = (idx + 1) % n
    return models[idx]


def _clean(text: str) -> str:
    """Pre-processing: strip <think>...</think> blocks from reasoning model output.

    Mirror of tools.py:clean_output — applied here inside _invoke() so every
    GENERATE equivalent automatically returns clean text.
    In SPL this is an explicit CALL clean_output(@var) INTO @var after each GENERATE.
    """
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    return cleaned if cleaned else text.strip()


def _extract_score(text: str) -> float:
    """Extract the last numeric value from a pre-cleaned score string."""
    nums = re.findall(r"\d+\.?\d*", text)
    return float(nums[-1]) if nums else 0.0


def _write(path: str, content: str) -> None:
    """Mirror of SPL built-in CALL write_file()."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def _invoke(model: str, prompt: str) -> str:
    """Single LLM call with automatic <think> pre-processing.

    In SPL: GENERATE f() USING MODEL @m INTO @var
            CALL clean_output(@var) INTO @var   -- explicit pre-processing step
    In LangGraph: pre-processing is hidden inside this helper.
    """
    raw = ChatOllama(model=model).invoke(prompt).content
    return _clean(raw)


# ─── Nodes  (each mirrors one GENERATE block + CALL write_file in the WORKFLOW) ─

def node_generate(state: EnsembleState) -> dict:
    i         = state["current_index"]
    gen_model = _pick_model(state["models"], "", state["random_selection"], i)
    print(f"[Candidate {i}] generating with model={gen_model}")

    answer = _invoke(gen_model, ANSWER_CANDIDATE.format(question=state["question"]))
    _write(f"{state['log_dir']}/candidate_{i}.md",
           f"# Candidate {i} — model: {gen_model}\n\n{answer}")

    return {
        "candidates": state["candidates"] + [answer],
        "gen_models": state["gen_models"] + [gen_model],
    }


def node_score(state: EnsembleState) -> dict:
    i          = state["current_index"]
    gen_model  = state["gen_models"][i]
    score_model = _pick_model(state["models"], gen_model, state["random_selection"], i)
    print(f"[Candidate {i}] scoring  with model={score_model}")

    score = _invoke(score_model, SCORE_CANDIDATE.format(
        question=state["question"],
        answer=state["candidates"][i],
    ))
    _write(f"{state['log_dir']}/score_{i}.md",
           f"# Score for candidate {i}\n"
           f"Generator: {gen_model} | Scorer: {score_model}\n\n"
           f"Score: {score}")
    print(f"[Candidate {i}] score={_extract_score(score):.1f}")

    return {
        "scores":       state["scores"] + [score],
        "score_models": state["score_models"] + [score_model],
        "current_index": i + 1,
    }


def node_consensus(state: EnsembleState) -> dict:
    print("Finding consensus ...")
    text = "\n---\n".join(state["candidates"])
    consensus = _invoke(state["consensus_model"],
                        FIND_CONSENSUS.format(candidates=text))
    _write(f"{state['log_dir']}/consensus.md", consensus)
    return {"consensus": consensus}


def node_winner(state: EnsembleState) -> dict:
    """Deterministic argmax — mirror of CALL select_winner() in ensemble_v2.spl."""
    print("Selecting winner (deterministic argmax) ...")
    score_values = [_extract_score(s) for s in state["scores"]]
    best_idx     = score_values.index(max(score_values))
    best         = state["candidates"][best_idx]
    print(f"Winner: candidate {best_idx} "
          f"(score={score_values[best_idx]:.1f}, model={state['gen_models'][best_idx]})")
    _write(f"{state['log_dir']}/winner.md", best)
    return {"best_candidate": best}


def node_polish(state: EnsembleState) -> dict:
    print(f"Polishing with model={state['polish_model']} ...")
    final = _invoke(state["polish_model"], POLISH.format(
        question=state["question"],
        best_answer=state["best_candidate"],
        consensus=state["consensus"],
    ))
    _write(f"{state['log_dir']}/final_answer.md", final)
    return {"final_answer": final}


# ─── Conditional edge  (SPL: WHILE @i < @n_candidates DO) ────────────────────

def _loop_or_proceed(state: EnsembleState) -> str:
    return "generate" if state["current_index"] < state["n_candidates"] else "consensus"


# ─── Graph construction  (SPL: implicit in sequential WORKFLOW layout) ─────────

def build_graph():
    g = StateGraph(EnsembleState)

    g.add_node("generate",  node_generate)
    g.add_node("score",     node_score)
    g.add_node("consensus", node_consensus)
    g.add_node("winner",    node_winner)
    g.add_node("polish",    node_polish)

    g.set_entry_point("generate")
    g.add_edge("generate", "score")
    g.add_conditional_edges("score", _loop_or_proceed, {
        "generate":  "generate",
        "consensus": "consensus",
    })
    g.add_edge("consensus", "winner")
    g.add_edge("winner",    "polish")
    g.add_edge("polish",    END)

    return g.compile()


# ─── Entry point  (SPL: built into the CLI — `spl run ...`) ───────────────────

def main():
    p = argparse.ArgumentParser(description="Ensemble voting — LangGraph edition")
    p.add_argument("--question",         required=True)
    p.add_argument("--models",           nargs="+",
                   default=["llama3.2", "qwen2.5", "gemma3", "mistral", "deepseek-r1"])
    p.add_argument("--n-candidates",     type=int, default=5)
    p.add_argument("--random-selection",
                   type=lambda x: x.lower() not in ("false", "0", "no"), default=True)
    p.add_argument("--consensus-model",  default="qwen2.5")
    p.add_argument("--polish-model",     default="deepseek-r1")
    p.add_argument("--log-dir",          default="cookbook/20_ensemble_voting/logs")
    args = p.parse_args()

    graph = build_graph()

    result = graph.invoke({
        "question":         args.question,
        "models":           args.models,
        "n_candidates":     args.n_candidates,
        "random_selection": args.random_selection,
        "consensus_model":  args.consensus_model,
        "polish_model":     args.polish_model,
        "log_dir":          args.log_dir,
        # ── accumulators must be initialised explicitly in LangGraph ──────────
        "candidates":       [],
        "scores":           [],
        "gen_models":       [],
        "score_models":     [],
        "current_index":    0,
        # ── outputs ───────────────────────────────────────────────────────────
        "consensus":        "",
        "best_candidate":   "",
        "final_answer":     "",
    })

    print("\n" + "=" * 60)
    print(result["final_answer"])


if __name__ == "__main__":
    main()
