"""Python tools for Recipe 20 v2: Ensemble Voting — Multi-Model Edition.

Two deterministic tools — zero LLM calls, zero hallucination risk:

  pick_model(models, exclude, random_selection, index)
      Selects a model from the pool in one of two modes:
        random_selection=true  → random pick, optionally excluding one model
        random_selection=false → positional pick by index (mod pool size),
                                 advances by +1 when the slot matches exclude
      Used twice per candidate iteration:
        1. pick generator model  (exclude='')
        2. pick scorer model     (exclude=@gen_model — no self-grading)

  select_winner(candidates, scores)
      Pure argmax over numeric scores — deterministic winner selection.
      Candidates are ||| -separated; scores are comma-separated floats.

Load with:
    spl run cookbook/20_ensemble_voting/ensemble_v2.spl \\
        --adapter ollama \\
        --tools cookbook/20_ensemble_voting/tools.py \\
        question="What causes inflation?"

    # Positional / reproducible mode
    spl run cookbook/20_ensemble_voting/ensemble_v2.spl \\
        --adapter ollama \\
        --tools cookbook/20_ensemble_voting/tools.py \\
        question="What causes inflation?" \\
        random_selection=false
"""

import json
import random
import re

from spl.tools import spl_tool


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _parse_models(models: str) -> list[str]:
    """Parse models from a LIST (JSON array string) or comma-separated TEXT.

    SPL serialises LIST inputs as a JSON array, e.g. '["llama3.2","gemma3"]'.
    Plain TEXT inputs arrive as 'llama3.2,gemma3'.  Both forms are handled.
    """
    raw = models.strip()
    if raw.startswith("["):
        try:
            parsed = json.loads(raw)
            return [str(m).strip() for m in parsed if str(m).strip()]
        except (json.JSONDecodeError, TypeError):
            pass
    return [m.strip() for m in raw.split(",") if m.strip()]


def _clean(text: str) -> str:
    """Strip <think>...</think> blocks produced by reasoning models (deepseek-r1, etc.).

    Applied as a pre-processing step so all downstream code — score parsing,
    log files, consensus, polish — sees clean text only.
    Falls back to the original text if stripping leaves nothing.
    """
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    return cleaned if cleaned else text.strip()


def _extract_score(text: str) -> float:
    """Extract the last numeric value from a (pre-cleaned) score string.

    Expects text already stripped of <think> blocks via _clean().
    Takes the last number found — the model's final verdict after any prose.
    """
    nums = re.findall(r"\d+\.?\d*", text)
    return float(nums[-1]) if nums else 0.0


# ─── Tools ────────────────────────────────────────────────────────────────────

@spl_tool
def clean_output(text: str) -> str:
    """Pre-processing tool: strip <think>...</think> blocks from LLM output.

    Call this immediately after any GENERATE that may use a reasoning model
    (deepseek-r1, qwen3, etc.) to ensure downstream steps see clean text.

    Usage in SPL:
        GENERATE score_candidate(@candidate, @question) USING MODEL @score_model INTO @score
        CALL clean_output(@score) INTO @score
    """
    return _clean(text)


@spl_tool
def pick_model(
    models: str,
    exclude: str = "",
    random_selection: str = "true",
    index: str = "0",
) -> str:
    """Pick a model from the pool in random or positional mode.

    Args:
        models:           Comma-separated or JSON-array list of model names.
        exclude:          Model to avoid (generator model when picking scorer).
        random_selection: 'true'  → random draw (default, simulates diversity)
                          'false' → positional by index mod pool size
        index:            Current candidate index (used in positional mode).

    Returns:
        A single model name string.

    Positional mode rotation example (5 models, 5 candidates, no exclude):
        i=0 → models[0], i=1 → models[1], ..., i=4 → models[4]

    Positional mode with exclude (scorer picking, exclude = generator at i):
        Scorer advances one slot: models[(i + 1) % n]
        This guarantees scorer != generator as long as pool has >= 2 models.
    """
    choices = _parse_models(models)
    if not choices:
        return "gemma3"  # safe fallback

    exc = exclude.strip()

    if random_selection.strip().lower() in ("false", "0", "no"):
        # ── Positional mode ────────────────────────────────────────────────
        n = len(choices)
        idx = int(index) % n
        if exc and choices[idx] == exc:
            # Advance one slot to avoid the excluded model
            idx = (idx + 1) % n
        return choices[idx]

    # ── Random mode (default) ─────────────────────────────────────────────
    filtered = [m for m in choices if m != exc]
    if not filtered:
        filtered = choices  # single-model pool: allow repeat
    return random.choice(filtered)


@spl_tool
def select_winner(candidates: str, scores: str) -> str:
    """Return the candidate with the highest numeric score.

    Deterministic argmax — no LLM involved, no hallucination risk.

    Args:
        candidates: Candidate texts joined by  |||  (pipe-pipe-pipe).
        scores:     Comma-separated score values, one per candidate.

    Returns:
        The full text of the winning candidate.
    """
    cand_list = [c.strip() for c in candidates.split("|||") if c.strip()]
    score_parts = [s.strip() for s in scores.split("|||") if s.strip()]

    if not cand_list:
        return ""

    # Parse scores; pad with 0.0 if counts mismatch
    score_values = [_extract_score(s) for s in score_parts]
    while len(score_values) < len(cand_list):
        score_values.append(0.0)

    best_idx = score_values.index(max(score_values))
    return cand_list[best_idx]
