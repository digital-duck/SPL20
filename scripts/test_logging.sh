#!/usr/bin/env bash
# test_logging.sh — Run the 6 recipes that write intermediate logs to sub-folders.
#
# Usage (from repo root):
#   bash scripts/test_logging.sh
#   bash scripts/test_logging.sh --model llama3.2
#
# Each recipe's console output is tee'd to cookbook/out/
# Each recipe's intermediate artifacts land in cookbook/XX_name/logs/

set -euo pipefail

ADAPTER="ollama"
MODEL="gemma3"
COOKBOOK="cookbook"
OUT_DIR="${COOKBOOK}/out"
# Allow --model override
while [[ $# -gt 0 ]]; do
  case $1 in
    --model|-m) MODEL="$2"; shift 2 ;;
    --adapter)  ADAPTER="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

mkdir -p "$OUT_DIR"

run_recipe() {
  local id="$1"
  local name="$2"
  local log_label="$3"
  shift 3
  local args=("$@")

  echo ""
  echo "============================================================"
  echo "  Recipe #${id}: ${name}"
  echo "============================================================"

  local ts=$(date +%Y%m%d_%H%M%S)
  local out="${OUT_DIR}/${log_label}-${ts}.md"
  spl run "${args[@]}" --adapter "$ADAPTER" -m "$MODEL" \
    2>&1 | tee "$out"

  echo ""
  echo "  Console log : $out"
  echo "  Artifact dir: $(echo "${args[0]}" | cut -d/ -f1-2)/logs/"
}

# ── 05 Self-Refine ─────────────────────────────────────────────
run_recipe 05 "Self-Refine" "self_refine" \
  "${COOKBOOK}/05_self_refine/self_refine.spl" \
  "task=Write a short essay on the importance of sleep"

# ── 11 Debate Arena ────────────────────────────────────────────
run_recipe 11 "Debate Arena" "debate_arena" \
  "${COOKBOOK}/11_debate_arena/debate.spl" \
  "topic=AI should be open-sourced"

# ── 12 Plan and Execute ────────────────────────────────────────
run_recipe 12 "Plan and Execute" "plan_execute" \
  "${COOKBOOK}/12_plan_and_execute/plan_execute.spl" \
  "task=Build a REST API for a todo app"

# ── 13 Map-Reduce ──────────────────────────────────────────────
run_recipe 13 "Map-Reduce Summarizer" "map_reduce" \
  "${COOKBOOK}/13_map_reduce/map_reduce.spl" \
  --tools "${COOKBOOK}/13_map_reduce/tools.py" \
  "document=$(cat ${COOKBOOK}/13_map_reduce/large_doc.txt 2>/dev/null || echo 'Distributed AI inference is becoming increasingly important. Consumer GPUs offer a cost-effective alternative to centralized cloud providers. Key challenges include coordination, energy efficiency, and open standards.')" \
  "style=bullet points"

# ── 16 Reflection Agent ────────────────────────────────────────
run_recipe 16 "Reflection Agent" "reflection" \
  "${COOKBOOK}/16_reflection/reflection.spl" \
  "problem=Design a URL shortener system"

# ── 21 Multi-Model Pipeline ────────────────────────────────────
run_recipe 21 "Multi-Model Pipeline" "multi_model" \
  "${COOKBOOK}/21_multi_model_pipeline/multi_model.spl" \
  "topic=climate change"

# ── Summary ────────────────────────────────────────────────────
echo ""
echo "============================================================"
echo "  All 6 recipes complete. Artifact folders:"
echo "============================================================"
for dir in \
  "${COOKBOOK}/05_self_refine/logs" \
  "${COOKBOOK}/11_debate_arena/logs" \
  "${COOKBOOK}/12_plan_and_execute/logs" \
  "${COOKBOOK}/13_map_reduce/logs" \
  "${COOKBOOK}/16_reflection/logs" \
  "${COOKBOOK}/21_multi_model_pipeline/logs"
do
  if [ -d "$dir" ]; then
    count=$(ls "$dir" | wc -l)
    echo "  $dir  ($count files)"
  else
    echo "  $dir  (not created — check for errors above)"
  fi
done
echo ""
