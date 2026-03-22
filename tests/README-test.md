# SPL 2.0 Test Suite

231 tests across 12 test files. All tests run offline (no LLM or network required).

## Running Tests

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run a specific test file
pytest tests/test_parser.py

# Run a specific test class or method
pytest tests/test_executor.py::TestWorkflowExecution
pytest tests/test_executor.py::TestWorkflowExecution::test_evaluate_semantic

# Run with coverage
pytest tests/ --cov=spl --cov-report=term-missing
```

## Test Files

| File | Tests | Coverage |
|------|------:|----------|
| `test_lexer.py` | 31 | Tokenization: keywords, operators, strings, numbers, identifiers, edge cases |
| `test_parser.py` | 50 | Parsing: PROMPT, WORKFLOW, PROCEDURE, EVALUATE, WHILE, GENERATE INTO, COMMIT, CALL, DO/EXCEPTION, RAISE, RETRY, SELECT INTO, CTEs, CREATE FUNCTION, security/accounting metadata |
| `test_cli.py` | 31 | CLI commands: run, parse, validate, syntax, explain, adapters, init, memory, rag, text2spl, version; parameter parsing |
| `test_adapters.py` | 22 | Adapter registry, echo adapter, OpenRouter/Ollama/Momagrid/Anthropic/OpenAI/Google/DeepSeek/Qwen adapter registration and config |
| `test_executor.py` | 18 | PROMPT execution, WORKFLOW execution: EVALUATE (semantic + deterministic), WHILE loops, GENERATE INTO, COMMIT, RAISE/exception handling, variable state, CALL procedures |
| `test_analyzer.py` | 13 | Semantic validation: duplicate names, budget warnings, temperature bounds, exception type checking, security classification, condition type inference |
| `test_integration.py` | 13 | End-to-end: parse → analyze → optimize → execute for PROMPT and WORKFLOW patterns |
| `test_text2spl.py` | 12 | text2SPL compiler: validation pipeline (lex → parse → analyze), mode instructions, system prompt, compile-validate-retry loop |
| `test_storage.py` | 13 | SQLite memory store (CRUD, cache), FAISS vector store (add, query, count) |
| `test_optimizer.py` | 10 | Execution planning: token allocation, step ordering, workflow plans |
| `test_ir.py` | 10 | JSON serialization of AST and execution plans |
| `test_explain.py` | 8 | ASCII plan rendering for PROMPT and WORKFLOW statements |
| **Total** | **231** | |

## Architecture Coverage

```
Source Code              Test File                 Key Assertions
─────────────────────    ─────────────────────     ─────────────────────────────────
spl/lexer.py        →   test_lexer.py            115 token types, keyword-as-ident
spl/parser.py       →   test_parser.py           All SPL 1.0 + 2.0 constructs
spl/ast_nodes.py    →   test_parser.py           30+ AST node types
spl/analyzer.py     →   test_analyzer.py         Semantic rules, condition inference
spl/optimizer.py    →   test_optimizer.py        Token budgets, workflow plans
spl/executor.py     →   test_executor.py         PROMPT + WORKFLOW execution
spl/explain.py      →   test_explain.py          Plan rendering
spl/ir.py           →   test_ir.py               AST ↔ JSON round-trip
spl/cli.py          →   test_cli.py              All CLI commands
spl/text2spl.py     →   test_text2spl.py         NL → SPL compilation
spl/adapters/       →   test_adapters.py         Registry + 10 adapters
spl/storage/        →   test_storage.py          Memory + vector store
integration          →   test_integration.py      Full pipeline end-to-end
```

## LLM Adapters

All 10 adapters are registered and available:

| Adapter | Status | How to use |
|---------|--------|------------|
| `echo` | Built-in | `spl run file.spl` (default, no setup) |
| `claude_cli` | Built-in | `spl run file.spl --adapter claude_cli` |
| `ollama` | Built-in | `--adapter ollama` (needs Ollama running) |
| `anthropic` | Built-in | `export ANTHROPIC_API_KEY=...` then `--adapter anthropic` |
| `openai` | Built-in | `export OPENAI_API_KEY=...` then `--adapter openai` |
| `google` | Built-in | `export GOOGLE_API_KEY=...` then `--adapter google` |
| `deepseek` | Built-in | `export DEEPSEEK_API_KEY=...` then `--adapter deepseek` |
| `qwen` | Built-in | `export DASHSCOPE_API_KEY=...` then `--adapter qwen` |
| `openrouter` | Built-in | `export OPENROUTER_API_KEY=...` then `--adapter openrouter` |
| `momagrid` | Built-in | `export MOMAGRID_HUB_URL=...` then `--adapter momagrid` |

## Key Test Patterns

- **No LLM calls in tests**: All tests use the `echo` adapter or mock objects
- **Parser tests**: Parse SPL source → assert AST node types and field values
- **Executor tests**: Build AST programmatically → execute with echo adapter → assert results
- **CLI tests**: Use Click's `CliRunner` for isolated CLI invocation
- **Integration tests**: Full pipeline from `.spl` source string to execution results
