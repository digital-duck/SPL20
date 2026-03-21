
```bash
spl2 run cookbook/12_plan_and_execute/plan_execute.spl --adapter ollama -m qwen2.5-coder task=Build a REST API for a todo app output_dir=cookbook/12_plan_and_execute/output max_steps=4
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
LLM Calls: 43
Tokens: 12629 in / 4268 out
Latency: 63558ms
------------------------------------------------------------
```output
To build and run the REST API for a todo app, follow these steps:

First, create a new Python project directory and install the required packages by running `pip install fastapi uvicorn` in your terminal. Then, navigate to the project directory and run the command `uvicorn main:app --host 0.0.0.0 --port 8000` (assuming the FastAPI app is defined in a file named `main.py`). This will start the API server on port 8000.

Note: The specific files mentioned (api_endpoints.yml, /endpoints.md, schema.json) seem to be configuration and documentation files rather than code files. It's likely that these files are used to generate or configure the REST API endpoints, but their exact usage would depend on the implementation details not provided in this task description.
```
------------------------------------------------------------
Variables:
  @task = Build a REST API for a todo app
  @output_dir = cookbook/12_plan_and_execute/output
  @max_steps = 4
  @step_index = 4
  @results = 
## Step 0
This step produces a set of well-defined REST API endpoints for creating, reading, updating, and deleting (CRUD) operations on data. The resulting endpoint design will provide a solid foundation for the implementation.

File list:

* `api_endpoints.yml` or similar configuration file
* `/endpoints.md` documentation file (optional)
* Possibly `schema.json` or other schema definition files
## Step 1
This step defines a set of well-structured REST API endpoints for CRUD operations on data, providing a clear foundation for implementing the API. The resulting endpoint design ensures that each endpoint has a single responsibility and is easily identifiable by its URL pattern.

The output of this step includes:

* `api_endpoints.yml` or similar configuration file
* `/endpoints.md` documentation file (optional)
* Possibly `schema.json` or other schema definition files
## Step 2
This step defines a set of well-structured REST API endpoints for CRUD operations on data, providing a clear foundation for implementing the API. The resulting endpoint design ensures that each endpoint has a single responsibility and is easily identifiable by its URL pattern. This results in a solid API framework.

The output includes:
* `api_endpoints.yml` or similar configuration file
* `/endpoints.md` documentation file (optional)
* Possibly `schema.json` or other schema definition files.
## Step 3
This step provides a well-defined set of REST API endpoints for CRUD operations on data. The resulting endpoint design ensures each endpoint has a single responsibility and is easily identifiable by its URL pattern. The output includes a clear foundation for implementing the API.

The output includes:
* `api_endpoints.yml`
* `/endpoints.md` (optional)
* Possibly `schema.json`
  @plan = **Revised Plan**

Since Step 0 failed, we will skip it and start with Step 1.

**Step 1: Define Endpoints and Request/Response Schemas**
	* Define REST API endpoints for CRUD operations (e.g., /todos, /todos/{id})
	* Create request/response schemas using JSON Schema or Swagger
	* Ensure endpoint security requirements are met (e.g., authentication, rate limiting)
	* Review existing API documentation and industry standards to ensure compliance

**Step 2: Design Database Schema**
	* Choose a database management system (DBMS) to store todo data
	* Define the structure of tables for storing todo items and their associated metadata
	* Optimize schema for efficient querying and indexing
	* Consider implementing a data validation mechanism to ensure data consistency

**Step 3: Implement Todo Item Model and Business Logic**
	* Create a TodoItem model to represent individual todo items
	* Implement business logic for creating, updating, and deleting todo items (e.g., validation, error handling)
	* Consider applying domain-driven design principles to encapsulate todo item behavior
	* Integrate with the database schema to ensure data flow between models

**Step 4: Develop REST API using a Framework (e.g., Express.js, Nest.js)**
	* Set up the framework's basic structure and dependencies
	* Implement endpoint handlers for each defined endpoint
	* Use routing and middleware to manage request and response flow
	* Explore the use of API gateways or reverse proxies to enhance security and scalability

**Step 5: Test and Validate Endpoint Behavior**
	* Write unit tests for TodoItem model and business logic
	* Create integration tests for endpoints using a test client (e.g., Cypress, Postman)
	* Perform end-to-end testing to ensure seamless API usage
	* Use automated testing frameworks to streamline testing processes

**Step 6: Prepare for Deployment and Monitoring**
	* Configure logging and error handling mechanisms
	* Set up monitoring tools (e.g., Prometheus, Grafana) for API performance and latency
	* Ensure the API meets security requirements and adheres to industry standards
	* Develop a strategy for continuous integration and deployment (CI/CD) pipelines

**Step 7: Implement Security Measures**
	* Implement authentication mechanisms (e.g., OAuth, JWT)
	* Enable rate limiting and IP blocking to prevent abuse
	* Use HTTPS to encrypt data in transit
	* Conduct regular security audits and penetration testing to identify vulnerabilities

By skipping Step 0 and starting with Step 1, we can get the project back on track. We will revisit and refine our plan as needed to ensure a successful implementation of the REST API for the todo app.
  @step_count = 4
  @current_step = Define REST API endpoints for CRUD operations (e.g., /todos, /todos/{id})
  @step_result = This step provides a well-defined set of REST API endpoints for CRUD operations on data. The resulting endpoint design ensures each endpoint has a single responsibility and is easily identifiable by its URL pattern. The output includes a clear foundation for implementing the API.

The output includes:
* `api_endpoints.yml`
* `/endpoints.md` (optional)
* Possibly `schema.json`
  @validation = Passed
  @file_outline = 1. api_endpoints.yml - Configuration file defining REST API endpoints
2. /endpoints.md - Documentation file providing endpoint descriptions
3. schema.json - Schema definition files (optional)
  @file_count = 3
  @file_index = 3
  @current_file = api_endpoints.yml
Configuration file defining REST API endpoints
  @file_code = ```python
# filename: app/main.py

import fastapi
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid

app = FastAPI()

class TodoItem(BaseModel):
    id: str
    title: str
    description: str

class TodoList(BaseModel):
    items: list[TodoItem]

# Sample in-memory data store
todo_items = []
todo_lists = []

def get_id():
    return str(uuid.uuid4())

@app.post("/todos/")
async def create_todo(item: TodoItem):
    """Create a new todo item"""
    item.id = get_id()
    todo_items.append(item)
    return item

@app.get("/todos/")
async def read_todos():
    """Read all todo items"""
    return {"items": todo_items}

@app.get("/todos/{todo_id}")
async def read_todo(todo_id: str):
    """Read a specific todo item by id"""
    for item in todo_items:
        if item.id == todo_id:
            return item
    raise HTTPException(status_code=404, detail="Todo item not found")

@app.put("/todos/{todo_id}")
async def update_todo(todo_id: str, item: TodoItem):
    """Update a specific todo item by id"""
    for i, existing_item in enumerate(todo_items):
        if existing_item.id == todo_id:
            todo_items[i] = item
            return item
    raise HTTPException(status_code=404, detail="Todo item not found")

@app.delete("/todos/{todo_id}")
async def delete_todo(todo_id: str):
    """Delete a specific todo item by id"""
    for i, item in enumerate(todo_items):
        if item.id == todo_id:
            del todo_items[i]
            return {"message": "Todo item deleted"}
    raise HTTPException(status_code=404, detail="Todo item not found")

@app.get("/todo-lists/")
async def read_todo_lists():
    """Read all todo lists"""
    return {"lists": todo_lists}

@app.post("/todo-lists/")
async def create_todo_list(item: TodoList):
    """Create a new todo list"""
    item.id = get_id()
    todo_lists.append(item)
    return item

@app.get("/todo-lists/{todo_list_id}/items")
async def read_todo_items_in_list(todo_list_id: str):
    """Read all items in a specific todo list by id"""
    for i, list_item in enumerate(todo_lists):
        if list_item.id == todo_list_id:
            return {"items": [item.dict() for item in list_item.items]}
    raise HTTPException(status_code=404, detail="Todo list not found")

@app.put("/todo-lists/{todo_list_id}/items")
async def update_todo_items_in_list(todo_list_id: str, items: TodoList):
    """Update all items in a specific todo list by id"""
    for i, list_item in enumerate(todo_lists):
        if list_item.id == todo_list_id:
            list_item.items = items
            return {"message": "Items updated"}
    raise HTTPException(status_code=404, detail="Todo list not found")

@app.delete("/todo-lists/{todo_list_id}/items")
async def delete_todo_items_in_list(todo_list_id: str):
    """Delete all items in a specific todo list by id"""
    for i, list_item in enumerate(todo_lists):
        if list_item.id == todo_list_id:
            del list_item.items
            return {"message": "Items deleted"}
    raise HTTPException(status_code=404, detail="Todo list not found")
```
  @file_written = Written 1 file(s) to cookbook/12_plan_and_execute/output:
  app/main.py
============================================================
Log: /home/gongai/.spl/logs/plan_execute-ollama-20260321-024924.log
