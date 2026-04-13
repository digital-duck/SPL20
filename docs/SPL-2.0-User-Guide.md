# SPL 2.0 User Guide

Welcome to the **Structured Prompt Language (SPL) 2.0** User Guide. SPL 2.0 is a declarative, SQL-inspired language designed for orchestrating complex, multi-step agentic workflows with Large Language Models (LLMs).

---

## 1. Introduction

SPL 2.0 extends the original SPL with procedural control flow, making it "PL/SQL for LLMs." It allows you to define workflows that combine probabilistic LLM calls with deterministic tool usage, error handling, and iterative logic—all within a single, readable language.

### Key Benefits
- **Declarative**: Focus on *what* you want to achieve, not the boilerplate code.
- **Efficient**: Native support for token budget management and cost optimization.
- **Provider Agnostic**: Run the same `.spl` recipe on OpenAI, Anthropic, Google Gemini, Bedrock, Vertex AI, or local Ollama instances.
- **Agentic**: Built-in primitives for loops, semantic branching, and exception handling.

---

## 2. Core Concepts

### Workflows and Procedures
- **`WORKFLOW`**: The top-level entry point for an agentic process. It defines inputs, outputs, and a sequence of operations.
- **`PROCEDURE`**: Reusable sub-workflows that can be called from other workflows.

### LLM Invocation (`GENERATE`)
The `GENERATE` statement is used for probabilistic tasks—generating text, reasoning, or summarizing.
```sql
GENERATE summarize(@text) INTO @summary
```

### Deterministic Tools (`CALL`)
The `CALL` statement invokes deterministic Python tools or built-in functions. These cost **zero tokens**.
```sql
CALL list_append(@results, @current) INTO @results
```

### Control Flow
- **`EVALUATE`**: SQL-style branching based on numeric, string, or semantic (LLM-judged) conditions.
- **`WHILE`**: Iterative loops for refinement or batch processing.

### Error Handling
- **`EXCEPTION`**: Handle LLM failures like hallucinations, context overflows, or refusals gracefully.
- **`RETRY`**: Automatically re-attempt a failed step with different parameters (e.g., lower temperature).

---

## 3. Language Reference

### Workflow Structure
```sql
WORKFLOW research_agent
  INPUT: @topic TEXT, @depth NUMBER DEFAULT 3
  OUTPUT: @report TEXT
DO
  GENERATE research_plan(@topic) INTO @plan
  -- ... body ...
  RETURN @report WITH status = 'complete'
END
```

### Variables and Types
Variables are prefixed with `@` (e.g., `@my_var`).
- **`TEXT`**: Standard string content.
- **`NUMBER`**: Integer or floating-point values.
- **`BOOL`**: `TRUE` or `FALSE` literals.
- **`LIST`**: Native JSON-backed arrays (e.g., `['a', 'b']`).

### Assignment
```sql
@iteration := @iteration + 1
```

### F-Strings
Interpolate variables directly into strings:
```sql
LOGGING f'Processing chunk {@i} of {@total}'
```

### Built-in Functions
- **Lists**: `list_append`, `list_concat`, `list_count`, `list_get`.
- **Files**: `write_file(@path, @content)`, `read_file(@path)`.
- **Strings**: `upper`, `lower`, `truncate`, `len`.

---

## 4. Advanced Features

### Semantic Branching
Use `EVALUATE` with string literals to let an LLM judge the condition:
```sql
EVALUATE @feedback
  WHEN 'satisfactory' THEN
    RETURN @result
  ELSE
    GENERATE refine(@result, @feedback) INTO @result
END
```

### Exception Handling
Protect your workflows from common LLM issues:
```sql
EXCEPTION
  WHEN HallucinationDetected THEN
    RETRY WITH temperature = 0.1 LIMIT 3
  WHEN ContextLengthExceeded THEN
    LOGGING 'Input too large' LEVEL ERROR
END
```

### Multi-Model Pipelines
Specify different models for different steps:
```sql
GENERATE analyze(@data) USING MODEL 'gpt-4o' INTO @analysis
GENERATE summarize(@analysis) USING MODEL 'gemma3' INTO @summary
```

---

## 5. CLI Usage

### Running a Recipe
```bash
spl run my_agent.spl --adapter ollama -m llama3.2 topic="AI Safety"
```

### Validation and Planning
- `spl validate agent.spl`: Check for syntax errors.
- `spl explain agent.spl`: View the execution plan without calling an LLM.

### Interactive Studio
- `spl ui`: Launch the Text2SPL Knowledge Studio for natural language to SPL compilation.

---

## 6. Best Practices

1. **Deterministic First**: If you can do it with a `CALL` to a Python tool, do it. Save `GENERATE` for judgment and creative tasks.
2. **Set Budgets**: Always use `LIMIT n TOKENS` or specify `output_budget` in `GENERATE` to control costs.
3. **Log Everything**: Use `LOGGING ... LEVEL DEBUG` during development to trace state changes.
4. **Graceful Failures**: Always include an `EXCEPTION` block in production workflows.
5. **Reusable Logic**: Wrap complex sub-tasks in `PROCEDURE` blocks.
