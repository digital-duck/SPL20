# Recipe 00 — Recipe Maker (Meta-Recipe)

SPL 2.0 eating its own cake. The recipe-maker is a workflow that generates complete, runnable SPL recipes from a plain-language concept description. It is itself structured as a recipe — CALL to load context, GENERATE to create each component, CALL to write artifacts.

## What's in this recipe

| File | Purpose |
|---|---|
| `recipe_maker.spl` | Main SPL workflow — the meta-recipe |
| `tools.py` | Python tools: `load_patterns`, `load_dataset`, `load_resources`, `write_artifact`, `list_artifacts`, `notify_review` |
| `patterns.json` | Catalog of 11 SPL recipe patterns drawn from the existing 37-recipe cookbook |
| `readme.md` | This file |

## Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `concept` | TEXT | *(required)* | Plain-language description of the recipe to generate |
| `output_dir` | TEXT | `cookbook/output/` | Directory where generated artifacts are written |
| `dataset` | TEXT | `''` | Path to a local `.json`, `.csv`, or `.txt` file the recipe will operate on |
| `resources` | TEXT | `''` | Path to reference material, docs, or related work |
| `feedback` | TEXT | `human` | `human` (default) or `llm-judge` (v2) |

## Usage

Always pass `--tools tools.py`:

```bash
# Minimal — concept only
spl run cookbook/00_recipe_maker/recipe_maker.spl \
    --adapter ollama -m gemma3 \
    --tools cookbook/00_recipe_maker/tools.py \
    concept="Customer churn predictor with SHAP explainability" \
    output_dir="cookbook/38_churn_predictor/"

# With existing dataset
spl run cookbook/00_recipe_maker/recipe_maker.spl \
    --adapter ollama -m gemma3 \
    --tools cookbook/00_recipe_maker/tools.py \
    concept="Resume screener for software engineering roles" \
    dataset="data/resumes.json" \
    output_dir="cookbook/39_resume_screener/"

# With reference material
spl run cookbook/00_recipe_maker/recipe_maker.spl \
    --adapter ollama -m gemma3 \
    --tools cookbook/00_recipe_maker/tools.py \
    concept="Legal contract risk analyser" \
    resources="references/legal_risk_taxonomy.md" \
    output_dir="cookbook/40_contract_risk/"

# Regenerate an existing recipe (iterate mode)
spl run cookbook/00_recipe_maker/recipe_maker.spl \
    --adapter ollama -m gemma3 \
    --tools cookbook/00_recipe_maker/tools.py \
    concept="Improve recipe 28 support triage with priority routing" \
    dataset="cookbook/28_support_triage/orders.json" \
    output_dir="cookbook/28_support_triage_v2/"
```

## Workflow steps

```
concept + output_dir + dataset + resources
    │
    ├─ CALL load_patterns()          ← 11-pattern catalog — zero LLM cost
    ├─ CALL load_dataset()           ← user data context — zero LLM cost
    ├─ CALL load_resources()         ← reference material — zero LLM cost
    │
    ├─ GENERATE plan_recipe()        ← LLM: understand intent, choose pattern, design structure
    │
    ├─ GENERATE generate_spl_workflow()  ← LLM: write the .spl file
    ├─ GENERATE generate_tools_py()      ← LLM: write tools.py
    ├─ GENERATE generate_sample_data()   ← LLM: write data.json
    ├─ GENERATE generate_readme()        ← LLM: write readme.md
    │
    ├─ CALL write_artifact() × 5     ← write all files to output_dir — zero LLM cost
    ├─ CALL list_artifacts()         ← summarise bundle — zero LLM cost
    ├─ CALL notify_review()          ← format human review message — zero LLM cost
    │
    └─ COMMIT status=awaiting_review
    │
    │  ── v2 Placeholders ──────────────────────────────────────────────────
    │
    ├─ [v2] GENERATE validate_artifacts()   ← feedback gate (human or llm-judge)
    │           WHEN pass →
    │               GENERATE reflect()      ← lessons learned
    │               GENERATE publish_writeup() + CALL register_recipe()
    │           WHEN fail → RETRY
    └─ [v2] COMMIT status=published
```

## Generated artifacts

Each run produces a self-contained recipe bundle in `output_dir`:

| File | Contents |
|---|---|
| `workflow.spl` | The generated SPL workflow |
| `tools.py` | Python tools with `@spl_tool` decorators |
| `data.json` | Sample dataset (5–10 realistic records) |
| `readme.md` | Full recipe documentation |
| `recipe_plan.md` | The LLM's planning document (for debugging and iteration) |

## Pattern catalog (`patterns.json`)

The recipe-maker draws from 11 patterns distilled from the existing cookbook:

| Pattern | Category | Use when |
|---|---|---|
| `chain` | reasoning | Ordered stages: research → analyse → summarise |
| `self_refine` | agentic | Draft → critique → improve loop |
| `debate` | multi-agent | Explore trade-offs, stress-test a position |
| `plan_execute` | agentic | Complex tasks requiring decomposition |
| `map_reduce` | application | Batch processing, large documents |
| `evaluate_select` | benchmarking | Compare variants, pick winner |
| `guardrails` | safety | User-facing workflows with PII or harmful content risk |
| `rag` | retrieval | LLM needs real-world grounding data |
| `extraction` | application | Unstructured text → structured records |
| `multi_persona` | multi-agent | Role-based dialogue and collaboration |
| `tool_use` | agentic | Production hybrid: deterministic tools + LLM generation |

## The full recipe lifecycle (v1 → v3)

| Phase | Flag | Status |
|---|---|---|
| Generate | *(default)* | **v1 — implemented** |
| Taste | `--feedback human\|llm-judge` | v2 placeholder |
| Reflect | `--reflect` | v2 placeholder |
| Publish | `--publish` | v3 placeholder |

## Output status

| Status | Meaning |
|---|---|
| `awaiting_review` | Artifacts generated, human review required |
| `error` | GenerationError — check concept description |

## What the recipe-maker produces — and what it does not

The recipe-maker generates a **baseline** — a structurally complete starting point that covers the expected shape of the workflow, tools, data, and documentation. It is not a finished recipe.

Think of it as the first draft a chef sketches before cooking for real: the ingredients list is plausible, the steps are in the right order, but the seasoning needs adjusting, the timing needs testing, and some steps will only reveal their flaws once you actually run them.

**What you should expect to do after generation:**

- **Run it** — execute the generated workflow against the sample data and observe what breaks
- **Read the plan** — `recipe_plan.md` explains the LLM's reasoning; use it to understand intent before editing
- **Iterate on the tools** — the generated `tools.py` will often need schema adjustments, better error handling, or additional edge-case coverage
- **Refine the .spl** — GENERATE step names, parameter threading, and EVALUATE branches frequently need tuning
- **Expand the data** — the generated `data.json` covers the happy path; add edge cases, error cases, and realistic variation
- **Anneal** — run → observe → adjust → re-run, repeatedly, until the recipe reliably produces the output you want

The number of iterations depends on the complexity of the concept. Simple extraction or chain recipes may need only minor adjustments. Multi-persona simulations or domain-specific pipelines will need more passes. This is expected and normal — the recipe-maker compresses the bootstrap problem, not the craft problem.

## Baking tips

**Start with a recipe you already know.** Recreating an existing cookbook recipe is the ideal first test — you have ground truth to compare against and know exactly what a good result looks like. Try `28_support_triage` or `29_meeting_actions` first (simple, well-defined), then attempt something more complex like `33_interview_sim` to see how the recipe-maker handles multi-persona structure and scoring rubrics.

**Read `recipe_plan.md` before touching any code.** It captures the LLM's understanding of your concept before any code was written. A bad plan upstream explains almost every downstream problem — fix the plan first, then re-run rather than patching the generated artifacts around a flawed design.

**The interesting question isn't "how close" — it's "how many iterations to reach parity."** If a complex recipe needs 3 annealing passes to match a hand-crafted equivalent, that's a strong result. If it needs 10, the concept description or resources need richer grounding. Tune the input before tuning the output.

**What the comparison will reveal:**
- How well the plan step chose the right pattern
- Whether the generated `tools.py` got the `@spl_tool` signatures right without hand-holding
- How realistic the sample data is vs. what you would craft manually
- Whether the CALL/GENERATE split landed correctly without explicit guidance

**Use existing recipes as `--resources`.** If you are recreating or extending an existing recipe, pass the original `.spl` and `tools.py` as resources. The recipe-maker will use them as reference and produce a closer first draft.

**Complex recipes need more annealing — that is normal.** Simple chain or extraction recipes may converge in one or two passes. Multi-persona simulations, domain-specific pipelines, and anything with non-trivial scoring logic will need more. Budget for it rather than expecting a finished cake on the first bake.

## Design notes

The recipe-maker is intentionally a **v1 generate-only** implementation. The feedback, reflect, and publish phases are explicitly stubbed in the .spl file as commented-out v2 blocks, so the architecture is visible and ready to activate.

The `--feedback human` default keeps humans in the loop by design. The workflow does not auto-iterate — it generates, writes, notifies, and stops. The human decides whether to taste, iterate, or ship.

Files are written to `output_dir` with a `/tmp/spl_recipes/` fallback if the path is not writable. The actual path is always reported in the review notification.
