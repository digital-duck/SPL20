# Recipe 10 — Batch Test

Automated testing of all cookbook `.spl` scripts across multiple Ollama models. Perfect for CI/CD, model benchmarking, and regression testing.

## Usage

```bash
# Full test: all recipes x default models (gemma3, llama3.2)
bash cookbook/10_batch_test/batch_test.sh

# Single model
MODELS="gemma3" bash cookbook/10_batch_test/batch_test.sh

# Dry run with echo adapter (no Ollama needed)
ADAPTER=echo bash cookbook/10_batch_test/batch_test.sh

# Custom model set
MODELS="gemma3 llama3.2 mistral phi3" bash cookbook/10_batch_test/batch_test.sh
```

Output:
```
==============================================
  SPL 2.0 Batch Test
==============================================
  Adapter: ollama
  Models:  gemma3 llama3.2
  Time:    Wed Mar 18 2026
==============================================

>>> Model: gemma3
----------------------------------------------
  PASS  01_hello_world/hello.spl
  PASS  02_ollama_proxy/proxy.spl
  PASS  03_multilingual/multilingual.spl

>>> Model: llama3.2
----------------------------------------------
  PASS  01_hello_world/hello.spl
  PASS  02_ollama_proxy/proxy.spl
  PASS  03_multilingual/multilingual.spl

==============================================
  Results: 6/6 passed, 0 failed
==============================================
```
