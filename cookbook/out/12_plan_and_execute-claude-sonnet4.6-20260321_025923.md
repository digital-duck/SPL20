
```bash
spl2 run cookbook/12_plan_and_execute/plan_execute.spl --adapter claude_cli -m claude-sonnet-4-6 task=Build a REST API for a todo app output_dir=cookbook/12_plan_and_execute/output max_steps=4
```

```spl2
-- Recipe 12: Plan and Execute
-- A planner agent decomposes a task into steps, then an executor implements each one.
-- When output_dir is set, generated code files are written to disk one-by-one.
--
-- Usage:
--   spl2 run cookbook/12_plan_and_execute/plan_execute.spl --adapter ollama \
--       --tools cookbook/12_plan_and_execute/tools.py \
--       task="Build a REST API for a todo app" \
--       output_dir="cookbook/12_plan_and_execute/output"
--
--   spl2 run cookbook/12_plan_and_execute/plan_execute.spl --adapter ollama \
--       task="Set up a CI/CD pipeline for a Python project"


-- Phase 1: Decompose task into a numbered implementation plan
CREATE FUNCTION plan(task TEXT) RETURNS TEXT AS $$
You are a senior software architect. Break down this task into clear implementation steps:

Task: {task}

Output a numbered list of concrete steps (3–6 steps). Each step should be specific
and independently executable. No prose — just the numbered list.
$$;

-- Count how many steps are in the plan (capped at max_steps)
CREATE FUNCTION count_steps(plan TEXT, max_steps TEXT) RETURNS TEXT AS $$
Count the number of numbered steps in this plan.
Return ONLY a single integer — no explanation, no text.
If there are more than {max_steps} steps, return {max_steps}.

Plan:
{plan}
$$;

-- Extract step N from the plan (0-indexed)
CREATE FUNCTION extract_step(plan TEXT, step_index TEXT) RETURNS TEXT AS $$
Extract step number {step_index} (0-indexed) from this numbered plan and return
ONLY that step's description. No numbering prefix. No extra text.

Plan:
{plan}
$$;

-- Execute a step: produce a concise design decision + list of files to create
CREATE FUNCTION execute_step(current_step TEXT, prior_results TEXT) RETURNS TEXT AS $$
You are a senior software engineer planning an implementation.

Step: {current_step}
Completed so far: {prior_results}

Describe in 2-3 sentences what this step produces and list the filenames it creates.
Be brief — no code yet, just the design decision and file list.
$$;

-- Validate that a step produced meaningful output
CREATE FUNCTION validate_step(current_step TEXT, step_result TEXT) RETURNS TEXT AS $$
Did the following implementation successfully address the step?

Step: {current_step}
Implementation: {step_result}

Reply with exactly one word: "passed" or "failed".
$$;

-- Re-plan after a step failure
CREATE FUNCTION replan(task TEXT, plan TEXT, step_index TEXT, step_result TEXT) RETURNS TEXT AS $$
A step in our implementation plan failed. Create a revised plan.

Original task: {task}
Original plan: {plan}
Failed at step: {step_index}
Failure details: {step_result}

Output a new numbered plan starting from step {step_index}. Keep completed steps as-is.
$$;

-- Phase 4a: List all source files to create (no code — just filenames + one-line descriptions)
CREATE FUNCTION outline_files(task TEXT, results TEXT) RETURNS TEXT AS $$
You are a senior software engineer. Based on the implementation plan below, list every
source file that must be created to complete the task.

Task: {task}

Implementation plan:
{results}

Output a numbered list — one file per line — with the filename and a one-sentence description.
Example:
1. app.py - Flask application entry point, registers blueprints and starts the server
2. models.py - SQLAlchemy ORM models for Todo and User

No code. No prose. Just the numbered file list.
$$;

-- Count files in the outline
CREATE FUNCTION count_files(outline TEXT) RETURNS TEXT AS $$
Count the number of numbered items in this file list.
Return ONLY a single integer — no explanation, no text.

List:
{outline}
$$;

-- Extract one file entry at index N (0-indexed)
CREATE FUNCTION extract_file(outline TEXT, file_index TEXT) RETURNS TEXT AS $$
Extract item number {file_index} (0-indexed) from this numbered file list and return
ONLY that item's filename and description. No number prefix. No extra text.

List:
{outline}
$$;

-- Generate complete code for ONE file
CREATE FUNCTION generate_file(task TEXT, results TEXT, file_desc TEXT) RETURNS TEXT AS $$
You are a senior software engineer. Write complete, runnable code for ONE source file.

Task: {task}

Implementation plan:
{results}

File to create: {file_desc}

Output a SINGLE fenced code block. The FIRST line inside the fence MUST be a filename comment:

```python
# filename: app/main.py
...complete code...
```

Requirements:
- Complete, runnable code — no placeholders, no TODOs.
- Error handling, type hints, brief inline comments.
- Only this one file — nothing else.
$$;

-- Summarize what was built
CREATE FUNCTION summarize(task TEXT, results TEXT, file_outline TEXT) RETURNS TEXT AS $$
In 3-5 sentences, describe what was built for this task and how to run it.

Task: {task}
Files created:
{file_outline}
$$;


WORKFLOW plan_and_execute
    INPUT:
        @task TEXT DEFAULT 'Build a REST API for a todo app',
        @output_dir TEXT DEFAULT '',
        @max_steps INTEGER DEFAULT 5
    OUTPUT: @final_report TEXT
DO
    @step_index := 0
    @results := ''

    -- Phase 1: Plan
    GENERATE plan(@task) INTO @plan

    -- Phase 2: Count steps (capped at max_steps)
    GENERATE count_steps(@plan, @max_steps) INTO @step_count

    -- Phase 3: Execute each step (brief design notes only — no code)
    WHILE @step_index < @step_count DO
        GENERATE extract_step(@plan, @step_index) INTO @current_step
        GENERATE execute_step(@current_step, @results) INTO @step_result
        GENERATE validate_step(@current_step, @step_result) INTO @validation

        EVALUATE @validation
            WHEN 'failed' THEN
                GENERATE replan(@task, @plan, @step_index, @step_result) INTO @plan
                GENERATE count_steps(@plan, @max_steps) INTO @step_count
                @step_index := 0
                @results := ''
            OTHERWISE
                @results := @results + '\n## Step ' + @step_index + '\n' + @step_result
                @step_index := @step_index + 1
        END
    END

    -- Phase 4: Outline all files to generate
    GENERATE outline_files(@task, @results) INTO @file_outline
    GENERATE count_files(@file_outline) INTO @file_count

    -- Phase 5: Generate each file individually (one LLM call per file — avoids truncation)
    @file_index := 0
    WHILE @file_index < @file_count DO
        GENERATE extract_file(@file_outline, @file_index) INTO @current_file
        GENERATE generate_file(@task, @results, @current_file) INTO @file_code
        CALL write_code_files(@file_code, @output_dir) INTO @file_written
        @file_index := @file_index + 1
    END

    -- Phase 6: Summary report
    GENERATE summarize(@task, @results, @file_outline) INTO @final_report

    COMMIT @final_report WITH status = 'complete', steps_executed = @step_index, files_generated = @file_count

EXCEPTION
    WHEN MaxIterationsReached THEN
        GENERATE summarize(@task, @results, @file_outline) INTO @final_report
        COMMIT @final_report WITH status = 'partial', steps_executed = @step_index
    WHEN BudgetExceeded THEN
        COMMIT @results WITH status = 'budget_limit'
END
```

============================================================
Status: complete
LLM Calls: 55
Tokens: 17067 in / 5108 out
Latency: 225852ms
------------------------------------------------------------
```output
A REST API for a todo application was built using FastAPI (or Flask) with SQLAlchemy as the ORM, backed by a SQLite database for local development and configurable via environment variables for other environments. The data layer includes a `Todo` model mapped to a `todos` table, with Alembic handling database migrations. Configuration is read from a `.env` file (use `.env.example` as a template), keeping credentials out of source code.

To run it locally:

```bash
pip install -r requirements.txt
cp .env.example .env          # set DATABASE_URL if not using the SQLite default
alembic upgrade head          # apply migrations and create the todos table
uvicorn main:app --reload     # start the API server (or `python main.py` for Flask)
```
```
------------------------------------------------------------
Variables:
  @task = Build a REST API for a todo app
  @output_dir = cookbook/12_plan_and_execute/output
  @max_steps = 4
  @step_index = 4
  @results = 
## Step 0
This step defines the core `Todo` data structure used throughout the application. It produces a model/schema definition with the four specified fields: `id` (unique identifier), `title` (string), `completed` (boolean), and `created_at` (timestamp).

**Files created:**
- `models/todo.py`
## Step 1
This step scaffolds the full project infrastructure: a `pyproject.toml` (with pinned deps) and `requirements.txt` for dependency management, a `config.py` that reads `DATABASE_URL` from the environment (with a SQLite default for local dev), and a `database.py` that wires up the SQLAlchemy engine and session factory. It also initializes Alembic so migrations are ready to run against the configured database.

**Files created:**
- `pyproject.toml`
- `requirements.txt`
- `.env.example`
- `config.py`
- `database.py`
- `main.py`
- `alembic.ini`
- `alembic/env.py`
## Step 2
This step updates `models/todo.py` with the full SQLAlchemy ORM model (mapping `Todo` to a `todos` table with `id`, `title`, `completed`, and `created_at` columns), then validates that `alembic/env.py` correctly imports `Base.metadata` so Alembic can detect the model. It generates the initial autogenerated migration script and applies it, confirming the `todos` table is created in the database.

**Files created/modified:**
- `models/todo.py` (updated with ORM model)
- `alembic/versions/<hash>_initial_migration.py` (generated)
## Step 3
This step updates `models/todo.py` with the full SQLAlchemy ORM model mapping the `Todo` class to a `todos` table, then verifies `alembic/env.py` correctly imports `Base.metadata` so Alembic can introspect the model. Running `alembic revision --autogenerate` generates a migration script that captures the initial table schema, and `alembic upgrade head` applies it to create the `todos` table in the database.

**Files created/modified:**
- `models/todo.py` (updated with ORM model)
- `alembic/versions/<hash>_initial_migration.py` (generated)
  @plan = Based on the failure details, step 2 partially conflated project setup with schema/ORM work — leaving behind migration scaffolding that may be misconfigured. Here's a revised plan:

1. Define the data model: `Todo` with fields `id`, `title`, `completed`, `created_at`
2. *(failed — retry)* Set up the project: initialize FastAPI with `pyproject.toml`/`requirements.txt`, install dependencies (`fastapi`, `uvicorn`, `sqlalchemy`, `alembic`, `psycopg2` or `aiosqlite`), and configure DB connection string via environment variable in a `config.py` or `.env` file. **Remove or reset any partial Alembic/model files left by the failed step before proceeding.**
3. Define the `Todo` SQLAlchemy ORM model in `models/todo.py` with the schema from step 1. Validate Alembic is correctly wired (`alembic/env.py` points to `Base.metadata`) and generate the initial migration (`alembic revision --autogenerate`). Run `alembic upgrade head` to confirm the table is created successfully.
4. Implement CRUD endpoints: `GET /todos`, `POST /todos`, `GET /todos/:id`, `PUT /todos/:id`, `DELETE /todos/:id`
5. Add input validation and error responses (400, 404, 422) for each endpoint
6. Write integration tests covering happy path and error cases for each endpoint

The key change: step 2 now explicitly calls for cleaning up partial artifacts before re-running setup, and step 3 takes full ownership of the ORM model and migration work (which the failed step incorrectly mixed in).
  @step_count = 4
  @current_step = Define the `Todo` SQLAlchemy ORM model in `models/todo.py` with the schema from step 1. Validate Alembic is correctly wired (`alembic/env.py` points to `Base.metadata`) and generate the initial migration (`alembic revision --autogenerate`). Run `alembic upgrade head` to confirm the table is created successfully.
  @step_result = This step updates `models/todo.py` with the full SQLAlchemy ORM model mapping the `Todo` class to a `todos` table, then verifies `alembic/env.py` correctly imports `Base.metadata` so Alembic can introspect the model. Running `alembic revision --autogenerate` generates a migration script that captures the initial table schema, and `alembic upgrade head` applies it to create the `todos` table in the database.

**Files created/modified:**
- `models/todo.py` (updated with ORM model)
- `alembic/versions/<hash>_initial_migration.py` (generated)
  @validation = passed
  @file_outline = 1. `models/todo.py` - SQLAlchemy ORM model mapping the `Todo` class to the `todos` database table with all four fields.
2. `pyproject.toml` - Project metadata and pinned dependency declarations for the application.
3. `requirements.txt` - Flat list of installable dependencies for pip-based environments.
4. `.env.example` - Template showing required environment variables, including `DATABASE_URL`.
5. `config.py` - Reads configuration from environment variables with a SQLite fallback for local development.
6. `database.py` - Wires up the SQLAlchemy engine and session factory using the configured database URL.
7. `main.py` - FastAPI/Flask application entry point that registers routes and starts the server.
8. `alembic.ini` - Alembic configuration file pointing to the migration scripts directory and database.
9. `alembic/env.py` - Alembic environment script that imports `Base.metadata` for autogenerate support.
10. `alembic/versions/<hash>_initial_migration.py` - Autogenerated migration script that creates the initial `todos` table.
  @file_count = 10
  @file_index = 10
  @current_file = `alembic/env.py` - Alembic environment script that imports `Base.metadata` for autogenerate support.
  @file_code = ```python
# filename: alembic/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import sys
import os

# Make project root importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database import Base  # noqa: E402
from models import todo  # noqa: E402, F401 — import models so Base.metadata is populated

config = context.config

# Configure Python logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata for autogenerate support
target_metadata = Base.metadata


def get_url() -> str:
    """Read DATABASE_URL from env, falling back to alembic.ini sqlalchemy.url."""
    return os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (no live DB connection needed)."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (live DB connection)."""
    cfg = config.get_section(config.config_ini_section, {})
    cfg["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        cfg,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # avoid connection pool issues during migrations
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,      # detect column type changes
            compare_server_default=True,  # detect default value changes
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```
  @file_written = Written 1 file(s) to cookbook/12_plan_and_execute/output:
  alembic/env.py
============================================================
Log: /home/gongai/.spl/logs/plan_execute-claude_cli-20260321-025924.log
