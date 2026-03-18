#!/usr/bin/env bash
# Recipe 10: Batch Test
# Automated testing of all cookbook .spl scripts across multiple Ollama models.
# Perfect for CI/CD, model benchmarking, and regression testing.
#
# Usage:
#   bash cookbook/10_batch_test/batch_test.sh                    # all recipes, default models
#   MODELS="gemma3" bash cookbook/10_batch_test/batch_test.sh    # single model
#   ADAPTER=echo bash cookbook/10_batch_test/batch_test.sh       # dry run with echo

ADAPTER="${ADAPTER:-ollama}"
MODELS="${MODELS:-gemma3 llama3.2}"
COOKBOOK_DIR="$(cd "$(dirname "$0")/.." && pwd)"

TOTAL=0
PASSED=0
FAILED=0

echo "=============================================="
echo "  SPL 2.0 Batch Test"
echo "=============================================="
echo "  Adapter: $ADAPTER"
echo "  Models:  $MODELS"
echo "  Time:    $(date)"
echo "=============================================="
echo ""

# Collect all .spl files (skip workflow files that need specific params)
RECIPES=(
    "01_hello_world/hello.spl|"
    "02_ollama_proxy/proxy.spl|-p prompt=hello"
    "03_multilingual/multilingual.spl|-p user_input=hello -p lang=English"
)

for model in $MODELS; do
    echo ">>> Model: $model"
    echo "----------------------------------------------"

    for entry in "${RECIPES[@]}"; do
        IFS='|' read -r script params <<< "$entry"
        filepath="$COOKBOOK_DIR/$script"

        if [ ! -f "$filepath" ]; then
            echo "  SKIP  $script (not found)"
            continue
        fi

        TOTAL=$((TOTAL + 1))

        # Run and capture exit code
        if spl2 run "$filepath" --adapter "$ADAPTER" -m "$model" $params > /dev/null 2>&1; then
            echo "  PASS  $script"
            PASSED=$((PASSED + 1))
        else
            echo "  FAIL  $script"
            FAILED=$((FAILED + 1))
        fi
    done
    echo ""
done

echo "=============================================="
echo "  Results: $PASSED/$TOTAL passed, $FAILED failed"
echo "=============================================="

if [ $FAILED -gt 0 ]; then
    exit 1
fi
