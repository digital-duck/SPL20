# Gap Analysis: SPL 2.0 Implementation vs. Design Spec (v1.1)
**Date:** 2026-04-12

| Feature | Spec (v1.1) | Current Implementation | Status |
| :--- | :--- | :--- | :--- |
| **Operators** | `||` (Concat), `|` (Pipe) | Tokenized in `lexer.py` | **Missing in Parser/Executor** |
| **Semantic Eval** | `WHEN ~ 'is angry'` (v3.0) | `WHEN 'coherent'` (judge prompt) | **Partial (LLM-judged yes/no)** |
| **Commit/Return** | `COMMIT` names transaction | `RETURN` preferred; `COMMIT` as alias | **In Transition** |
| **RETRY** | `RETRY WITH temp=0.1 LIMIT 3` | `RetryStatement` node exists | **Partial (Executor logic limited)** |
| **Types** | `TEXT`, `NUMBER`, `BOOL`, `LIST`, `MAP` | All nodes present in `ast_nodes.py` | **Implemented** |
| **Momagrid** | Dimension 4: Distributed grid | `spl.adapters.momagrid.MomagridAdapter` | **Implemented** |
| **Procedural** | `WORKFLOW`, `PROCEDURE`, `CALL` | Full support in Parser/Executor | **Implemented** |
| **Built-ins** | `list_append`, `write_file`, etc. | Defined in `spl/functions.py` | **Implemented** |
| **F-Strings** | `f'text {@var}'` | Handled by Lexer and Executor | **Implemented** |
| **Exceptions** | `HallucinationDetected`, etc. | Defined and caught in `executor.py` | **Implemented** |

## Summary of Discrepancies

1.  **Pipelining (`|`)**: The v1.1 spec states the pipe operator is "implemented in v2.0." However, the parser and executor currently treat it as a reserved token but lack the logic to chain `GENERATE` calls.
2.  **Concatenation (`||`)**: While tokenized, the `BinaryOp` node and `_eval_expression` logic only handle arithmetic (`+`, `-`). The spec explicitly prefers `||` for string concatenation to avoid ambiguity with numeric addition.
3.  **RETRY Logic**: The `RETRY` statement supports `WITH` and `LIMIT` clauses in the grammar, but the `_handle_exception` logic in the executor needs to be enhanced to actually apply these overrides during the re-execution of the failed block.
4.  **Semantic Conditions**: The current implementation is actually "ahead" of the v3.0 timeline for basic semantic judgment (using a "yes/no" LLM prompt), but it lacks the `~` operator syntax mentioned in the spec.
5.  **COMMIT vs RETURN**: The codebase uses both, but the spec indicates a shift toward `RETURN` as the primary keyword for workflow finalization.
