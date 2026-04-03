# Recipe 30 — Code Generator + Tests

**Pattern:** Spec → Implementation → Review → Test Generation → Assembly

This recipe demonstrates a high-complexity sequential generation pipeline. In SPL, 
the entire flow from loading a specification to generating and verifying both 
code and tests is expressed in a single, readable script.

---

## The SPL Program

```sql
WORKFLOW code_gen_with_tests
DO
    -- 1. Resolve spec (inline or file)
    CALL load_spec(@spec) INTO @spec

    -- 2. Generate implementation
    GENERATE implement_function(...) INTO @implementation

    -- 3. Self-review and optional fix
    GENERATE review_implementation(...) INTO @review_notes
    EVALUATE @review_notes
        WHEN contains('issue') THEN GENERATE fix_implementation(...) INTO @implementation
    END

    -- 4. Generate tests
    GENERATE generate_tests(...) INTO @tests

    -- 5. Assemble final output
    GENERATE assemble_output(...) INTO @final_output
END
```

### Why SPL for Code Generation?

| Feature | SPL | LangGraph | AutoGen / CrewAI |
|---|---|---|---|
| **Data Flow** | Direct `@variable` passing | `TypedDict` state updates | Chat history or Task context |
| **Logic** | Native `EVALUATE` for fixes | Conditional edges | Python `if/else` |
| **Boilerplate** | Minimal (declarative) | High (Graph wiring) | Medium (Agent/Task setup) |
| **Brevity** | ~80 lines | ~150 lines | ~130 lines |

---

## Framework Comparison Highlights

### LangGraph
- **Pros:** Excellent for modeling the iterative "fix" loop as a persistent cycle; state is well-defined and verifiable.
- **Cons:** Significant boilerplate for what is largely a linear sequence of steps.

### AutoGen
- **Pros:** The conversation between a "Coder" and a "Reviewer" feels very natural and mimics human pair-programming.
- **Cons:** Orchestrating specific sequential steps (like "Generate Tests" only *after* "Fix Implementation") requires manual loop control in Python.

### CrewAI
- **Pros:** Task `context` allows the "Tester" agent to easily access both the "Spec" and the "Implementation" without manual wiring.
- **Cons:** Setup is verbose; requires defining specialized agents even if the underlying model is the same.

### SPL (Structured Prompt Language)
- **Pros:** **Winner on productivity.** SPL handles the most tedious parts of code generation pipelines—parameter passing between prompts and conditional branching—with native syntax. It reads like a technical design document but executes as code.
- **Cons:** Less focused on open-ended multi-turn "debates" than conversational frameworks.

---

## Running the Examples

### 1. SPL (Native)
```bash
spl run cookbook/30_code_gen/code_gen.spl \
    --adapter ollama -m gemma3 --tools cookbook/30_code_gen/tools.py \
    spec="A function that validates an email address"
```

### 2. LangGraph
```bash
python cookbook/30_code_gen/langgraph/code_gen_langgraph.py \
    --spec "A function that validates an email address"
```

### 3. AutoGen
```bash
python cookbook/30_code_gen/autogen/code_gen_autogen.py \
    --spec "A function that validates an email address"
```

### 4. CrewAI
```bash
python cookbook/30_code_gen/crewai/code_gen_crewai.py \
    --spec "A function that validates an email address"
```
