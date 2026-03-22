#!/usr/bin/env bash
# Recipe 04: Model Showdown
# Same prompt to multiple Ollama models — compare output quality and latency.
#
# Usage:
#   bash cookbook/04_model_showdown/showdown.sh "What is the meaning of life?"
#   bash cookbook/04_model_showdown/showdown.sh "Explain recursion in 3 sentences"
#   MODELS="gemma3 llama3.2 mistral" bash cookbook/04_model_showdown/showdown.sh "Write a haiku"

PROMPT="${1:-What is the meaning of life?}"
MODELS="${MODELS:-gemma3 llama3.2 mistral}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROXY="$SCRIPT_DIR/../../scripts/ollama_proxy.spl"

echo "=============================================="
echo "  SPL 2.0 Model Showdown"
echo "=============================================="
echo "  Prompt: $PROMPT"
echo "  Models: $MODELS"
echo "=============================================="
echo ""

for model in $MODELS; do
    echo ">>> $model"
    echo "----------------------------------------------"
    spl run "$PROXY" --adapter ollama -m "$model" prompt="$PROMPT"
    echo ""
done

echo "=============================================="
echo "  Showdown complete!"
echo "=============================================="
