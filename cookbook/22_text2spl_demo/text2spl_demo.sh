#!/usr/bin/env bash
# Recipe 22: text2SPL Compiler Demo
# Showcases the natural language → SPL 2.0 compiler.
#
# Usage:
#   bash cookbook/22_text2spl_demo/text2spl_demo.sh [adapter] [model]
#
# Requires: spl2 installed, Ollama running with gemma3 (or pass adapter/model)

set -uo pipefail

ADAPTER="${1:-ollama}"
MODEL="${2:-gemma3}"
OUTDIR="cookbook/22_text2spl_demo/generated"
mkdir -p "$OUTDIR"

PASS=0
FAIL=0

run_demo() {
    local num="$1" label="$2" desc="$3" mode="$4" outfile="$5"

    echo "--- Demo $num: $label ---"
    echo "  Input:  '$desc'"
    echo "  Mode:   $mode"
    echo ""

    # Use --no-validate so generation succeeds even if output has syntax issues;
    # we validate separately to show current maturity of each mode.
    if spl2 text2spl "$desc" \
        --adapter "$ADAPTER" -m "$MODEL" --mode "$mode" --no-validate -o "$outfile" 2>&1; then
        echo ""
        echo "  Validating generated code..."
        if spl2 parse "$outfile" 2>&1; then
            echo "  [validation: OK]"
        else
            echo "  [validation: warning — generated code has issues (known limitation for $mode mode)]"
        fi
        PASS=$((PASS + 1))   # generation succeeded; validation status is informational
    else
        echo "  [generation: FAILED]"
        FAIL=$((FAIL + 1))
    fi
    echo ""
}

echo "=== SPL 2.0 text2SPL Compiler Demo ==="
echo "    Adapter: $ADAPTER  Model: $MODEL"
echo ""

# --- Demo 1: Simple PROMPT (most reliable) ---
run_demo 1 "Compile a simple prompt" \
    "summarize a document with a 2000 token budget" \
    "prompt" "$OUTDIR/summarize.spl"

# --- Demo 2: WORKFLOW generation ---
run_demo 2 "Compile a multi-step workflow" \
    "build a review agent that drafts, critiques, and refines text until quality > 0.8" \
    "workflow" "$OUTDIR/review_agent.spl"

# --- Demo 3: Auto mode ---
run_demo 3 "Auto mode — LLM decides the best form" \
    "classify user intent and route to the right handler" \
    "auto" "$OUTDIR/classifier.spl"

# --- Summary ---
echo "=== Generated files ==="
ls -la "$OUTDIR"/*.spl 2>/dev/null || echo "  (no files generated)"
echo ""
echo "=== Demo complete: $PASS passed, $FAIL failed ==="
echo "  To view:    cat $OUTDIR/summarize.spl"
echo "  To execute: spl2 run $OUTDIR/summarize.spl --adapter $ADAPTER"

# Exit non-zero only if all demos failed
if [ "$PASS" -eq 0 ] && [ "$FAIL" -gt 0 ]; then
    exit 1
fi
