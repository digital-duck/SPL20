# Recipe 32 — Socratic Tutor

**Pattern:** Load Topic (deterministic) → Interactive Dialogue (LLM simulation) → Assessment → Adaptive Response

This recipe demonstrates a complex interactive dialogue simulation. In SPL, the 
interplay between deterministic tools (loading educational standards) and 
probabilistic steps (tutor/student turns) is managed in a single clear script.

---

## The SPL Program

```sql
WORKFLOW socratic_tutor
DO
    -- 1. Deterministic prep (0 tokens)
    CALL load_topic(@topic_id, @subject) INTO @topic_context
    CALL get_level_guidance(@student_level) INTO @level_guide

    -- 2. Opening interaction
    GENERATE opening_question(...) INTO @question_1
    GENERATE simulate_student_response(@question_1, ...) INTO @student_1

    -- 3. Adaptive follow-up
    GENERATE assess_understanding(@student_1, ...) INTO @understanding_score
    EVALUATE @understanding_score
        WHEN > 7 THEN GENERATE consolidation_question(...) INTO @question_3
        ELSE          GENERATE hint_question(...) INTO @question_3
    END
END
```

### Why SPL for Educational Workflows?

| Feature | SPL | LangGraph | AutoGen / CrewAI |
|---|---|---|---|
| **Context Injection** | Native `CALL` for topic data | Node functions must pass state | Manual setup before chat starts |
| **Dialogue Control** | Explicitly ordered `GENERATE` calls | State graph nodes | Conversational turns (can drift) |
| **Adaptivity** | Native `EVALUATE` | Conditional edges | Python `if/else` |
| **Brevity** | ~100 lines | ~180 lines | ~150 lines |

---

## Framework Comparison Highlights

### LangGraph
- **Pros:** Graph structure perfectly mirrors the "turns" of a dialogue; state persistence allows for resuming a session.
- **Cons:** Extremely high boilerplate for a simple 3-turn exchange; defining every student/tutor response as a node feels repetitive.

### AutoGen
- **Pros:** Naturally models the "Student" and "Tutor" as distinct conversational entities.
- **Cons:** Hard to force a strict sequential structure (Q1 -> A1 -> Q2 -> A2) without manual turn control in Python; extracting specific variables for the final compilation requires parsing chat history.

### CrewAI
- **Pros:** Persona-driven design makes the "Socratic Tutor" backstory very easy to implement.
- **Cons:** Not designed for interactive loops where one agent must wait for another's simulated response; requires re-instantiating the Crew for every turn to maintain control.

### SPL (Structured Prompt Language)
- **Pros:** **Winner on readability and control.** SPL allows the developer to precisely orchestrate an educational interaction. It combines the rigor of standard software (deterministic data loading) with the flexibility of LLMs (persona-based generation) in a way that is far more concise than any library.
- **Cons:** Best for structured pedagogical paths; less suitable for completely unconstrained "chat-with-anyone" scenarios.

---

## Running the Examples

### 1. SPL (Native)
```bash
spl run cookbook/32_socratic_tutor/socratic_tutor.spl \
    --adapter ollama --model gemma3 --tools cookbook/32_socratic_tutor/tools.py \
    topic_id="recursion" subject="programming"
```

### 2. LangGraph
```bash
python cookbook/32_socratic_tutor/langgraph/socratic_langgraph.py \
    --topic_id "recursion" --subject "programming"
```

### 3. AutoGen
```bash
python cookbook/32_socratic_tutor/autogen/socratic_autogen.py \
    --topic_id "recursion" --subject "programming"
```

### 4. CrewAI
```bash
python cookbook/32_socratic_tutor/crewai/socratic_crewai.py \
    --topic_id "recursion" --subject "programming"
```
