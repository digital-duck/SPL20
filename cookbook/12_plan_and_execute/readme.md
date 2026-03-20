# Recipe 12: Plan and Execute

A planner agent decomposes a complex task into steps; an executor runs each step sequentially with validation. Failed steps trigger automatic re-planning.

## Pattern

```
plan(task) → @plan
  └─► count_steps(@plan) → N
        └─► for each step:
              extract_step → execute_step → validate_step
                ├─ failed  → replan → restart
                └─ ok      → accumulate results
                      └─► synthesize(task, results)
```

## Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `task` | TEXT | *(required)* | The complex task to decompose and execute |

## Usage

```bash
spl2 run cookbook/12_plan_and_execute/plan_execute.spl --adapter ollama \
    task="Build a REST API for a todo app"

spl2 run cookbook/12_plan_and_execute/plan_execute.spl --adapter ollama \
    task="Set up a CI/CD pipeline for a Python project"

spl2 run cookbook/12_plan_and_execute/plan_execute.spl --adapter ollama \
    task="Migrate a MySQL database to PostgreSQL"
```

## Output status

| Status | Meaning |
|---|---|
| `complete` | All steps executed successfully |
| `partial` | Max iterations hit mid-execution |
| `budget_limit` | Token budget exceeded |
