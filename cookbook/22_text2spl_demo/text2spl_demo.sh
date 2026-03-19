#!/usr/bin/env bash
# Recipe 22: text2SPL Compiler Demo
# Showcases the natural language → SPL 2.0 compiler.
#
# Usage:
#   bash cookbook/22_text2spl_demo/text2spl_demo.sh
#
# Requires: Ollama running with at least one model (gemma3 recommended)

set -euo pipefail

ADAPTER="${1:-ollama}"
MODEL="${2:-gemma3}"
OUTDIR="cookbook/22_text2spl_demo/generated"
mkdir -p "$OUTDIR"

echo "=== SPL 2.0 text2SPL Compiler Demo ==="
echo "    Adapter: $ADAPTER  Model: $MODEL"
echo ""

# --- Demo 1: Simple PROMPT ---
echo "--- Demo 1: Compile a simple prompt ---"
echo "  Input:  'summarize a document with a 2000 token budget'"
echo ""
spl2 text2spl "summarize a document with a 2000 token budget" \
  --adapter "$ADAPTER" -m "$MODEL" --mode prompt -o "$OUTDIR/summarize.spl"
echo ""
echo "  Validating generated code..."
spl2 parse "$OUTDIR/summarize.spl"
echo ""

# --- Demo 2: WORKFLOW generation ---
echo "--- Demo 2: Compile a multi-step workflow ---"
echo "  Input:  'build a review agent that drafts, critiques, and refines text until quality > 0.8'"
echo ""
spl2 text2spl "build a review agent that drafts, critiques, and refines text until quality > 0.8" \
  --adapter "$ADAPTER" -m "$MODEL" --mode workflow -o "$OUTDIR/review_agent.spl"
echo ""
echo "  Validating generated code..."
spl2 parse "$OUTDIR/review_agent.spl"
echo ""

# --- Demo 3: Auto mode (LLM decides prompt vs workflow) ---
echo "--- Demo 3: Auto mode — LLM decides the best form ---"
echo "  Input:  'classify user intent and route to the right handler'"
echo ""
spl2 text2spl "classify user intent and route to the right handler" \
  --adapter "$ADAPTER" -m "$MODEL" --mode auto -o "$OUTDIR/classifier.spl"
echo ""
echo "  Validating generated code..."
spl2 parse "$OUTDIR/classifier.spl"
echo ""

# --- Summary ---
echo "=== Generated files ==="
ls -la "$OUTDIR"/*.spl 2>/dev/null || echo "  (no files generated)"
echo ""
echo "=== Demo complete ==="
echo "  To view generated code:  cat $OUTDIR/summarize.spl"
echo "  To execute generated code:  spl2 run $OUTDIR/summarize.spl --adapter $ADAPTER"
