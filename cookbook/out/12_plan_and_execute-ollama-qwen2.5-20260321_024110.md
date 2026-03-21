
```bash
spl2 run cookbook/12_plan_and_execute/plan_execute.spl --adapter ollama -m qwen2.5-coder task=Build a REST API for a todo app output_dir=cookbook/12_plan_and_execute/output max_steps=4
```

```spl2
-- Recipe 12: Plan and Execute
-- A planner agent decomposes a task into steps, then an executor implements each one.
-- When output_dir is set, generated code files are written to disk.
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

-- Synthesize: write a brief summary then generate ALL code files at once
CREATE FUNCTION synthesize(task TEXT, results TEXT) RETURNS TEXT AS $$
You are a senior software engineer. Based on the implementation plan below, write the complete working code.

Task: {task}

Implementation plan:
{results}

Output:
1. A 3-5 sentence summary of what was built and how to run it.
2. ALL source files as fenced code blocks. Each block MUST start with a filename comment as its FIRST line:

```python
# filename: app/main.py
...code...
```

Requirements:
- Complete, runnable code — no placeholders, no TODOs.
- Error handling, type hints, brief inline comments.
- One fenced block per file.
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

    -- Phase 3: Execute each step
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

    -- Phase 4: Synthesize
    GENERATE synthesize(@task, @results) INTO @final_report

    -- Phase 5: Write code files to disk (only when output_dir is provided)
    CALL write_code_files(@final_report, @output_dir) INTO @files_written

    COMMIT @final_report WITH status = 'complete', steps_executed = @step_index, files = @files_written

EXCEPTION
    WHEN MaxIterationsReached THEN
        GENERATE synthesize(@task, @results) INTO @final_report
        CALL write_code_files(@final_report, @output_dir) INTO @files_written
        COMMIT @final_report WITH status = 'partial', files = @files_written
    WHEN BudgetExceeded THEN
        COMMIT @results WITH status = 'budget_limit'
END
```

============================================================
Status: complete
LLM Calls: 135
Tokens: 43941 in / 10583 out
Latency: 162139ms
------------------------------------------------------------
```output
Here is the complete working code for a REST API for a todo app:

```python
# filename: requirements.txt
 Flask==2.0.1 
requests==2.27.1
sqlite3==3.36.0
```

```python
# filename: models.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(10), default="pending", nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp(), nullable=False)
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp(), nullable=False)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password = db.Column(db.String(140), nullable=False)
    roles = db.relationship('Role', backref='user', lazy=True)

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    todo_id = db.Column(db.Integer, db.ForeignKey('todo.id'), nullable=False)

db.create_all()
```

```python
# filename: routes.py
from flask import Blueprint, jsonify, request
from app.models import Todo, User, Role, Comment

routes = Blueprint('routes', __name__)

@routes.route('/todos', methods=['GET'])
def get_todos():
    todos = Todo.query.all()
    return jsonify([todo.to_dict() for todo in todos])

@routes.route('/todos/<int:todo_id>', methods=['GET'])
def get_todo(todo_id):
    todo = Todo.query.get(todo_id)
    if not todo:
        return jsonify({"error": "Todo not found"}), 404
    return jsonify(todo.to_dict())

@routes.route('/todos', methods=['POST'])
def create_todo():
    data = request.json
    if 'title' not in data or 'description' not in data:
        return jsonify({"error": "Missing fields"}), 400
    todo = Todo(title=data['title'], description=data['description'])
    db.session.add(todo)
    db.session.commit()
    return jsonify(todo.to_dict())

@routes.route('/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    todo = Todo.query.get(todo_id)
    if not todo:
        return jsonify({"error": "Todo not found"}), 404
    data = request.json
    if 'title' in data:
        todo.title = data['title']
    if 'description' in data:
        todo.description = data['description']
    db.session.commit()
    return jsonify(todo.to_dict())

@routes.route('/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    todo = Todo.query.get(todo_id)
    if not todo:
        return jsonify({"error": "Todo not found"}), 404
    db.session.delete(todo)
    db.session.commit()
    return jsonify({"message": "Todo deleted"})

@routes.route('/users', methods=['POST'])
def create_user():
    data = request.json
    if 'username' not in data or 'password' not in data:
        return jsonify({"error": "Missing fields"}), 400
    user = User(username=data['username'], password=data['password'])
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict())

@routes.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user.to_dict())

@routes.route('/comments', methods=['POST'])
def create_comment():
    data = request.json
    if 'text' not in data or 'user_id' not in data or 'todo_id' not in data:
        return jsonify({"error": "Missing fields"}), 400
    comment = Comment(text=data['text'], user_id=data['user_id'], todo_id=data['todo_id'])
    db.session.add(comment)
    db.session.commit()
    return jsonify(comment.to_dict())

@routes.route('/comments/<int:comment_id>', methods=['GET'])
def get_comment(comment_id):
    comment = Comment.query.get(comment_id)
    if not comment
```
------------------------------------------------------------
Variables:
  @task = Build a REST API for a todo app
  @output_dir = cookbook/12_plan_and_execute/output
  @max_steps = 4
  @step_index = 4
  @results = 
## Step 0
This step results in a revised programming language and framework selection plan that considers alternative solutions to meet the project's requirements.

Created files:

* Revised Language & Framework Selection Plan document (.docx)
* Alternative Solution Matrix table (spreadsheet or Excel file)
## Step 1
This step revises the programming language and framework selection process to consider alternative solutions that can meet the project's requirements. It results in a plan that takes into account potential trade-offs and optimizations. The goal is to identify a suitable alternative solution.

Created files:

* Revised Language & Framework Selection Plan document (.docx)
* Alternative Solution Matrix table (Excel file)
## Step 2
This step produces a revised plan for selecting a programming language and framework that considers alternative solutions to meet the project's requirements. The goal is to identify a suitable alternative solution that takes into account potential trade-offs and optimizations.

Created files:

* Revised Language & Framework Selection Plan document (.docx)
* Alternative Solution Matrix table (Excel file)
## Step 3
This step refines the database schema design to include additional features such as Todo item status, User roles and permissions, and a commenting system with user authentication for comments. The resulting plan will provide a solid foundation for the project's data storage and management.

Created files:
* Revised Database Schema Design document (.docx)
* Alternative Solution Matrix table (Excel file)
  @plan = Revised Implementation Plan:

**Step 1: Determine Programming Language and Framework**

* Failed: Yes
* Task Description: Re-evaluate the programming language and framework selection process to determine an alternative solution that can meet the project's requirements.

Output:
	+ `language_selection.txt`
	+ `framework_choice.json`
	+ `tech_stack.md`

**Step 2: Choose Programming Language and Framework**

* Revised: Yes
* Output:
	+ `language_selection.txt`
	+ `framework_choice.json`
	+ `tech_stack.md`

**Step 3: Design Database Schema**

* Original Plan: Completed
* Added Step to Refine Design: No
* New Task:
    - Refine database schema design to include additional features such as:
        * Todo item status (e.g., "in_progress", "done")
        * User roles and permissions
        * Commenting system with user authentication for comments
    - Evaluate the chosen database schema against various constraints, such as data consistency, scalability, and performance.
* Output:
	+ Database Schema Design Document
	+ Entity-Relationship Diagram
	+ SQL Script

**Step 4: Design API Endpoints**

* Original Plan: Revised and Updated
* Additional Task to Implement Pagination:
    - Implement pagination for the GET /todos endpoint to retrieve a paginated list of all users' todos, including pagination metadata.
* Output:
	+ Revised API Endpoints Document
	+ Pagination Implementation Code

**Step 5: Implement Authentication and Authorization**

* Original Plan: Revised
* New Task to Research Authentication Mechanism:
    - Research and implement an authentication mechanism, such as OAuth or JWT.
* Output:
	+ Authentication and Authorization Mechanism Document

**Step 6: Test and Deploy API**

* Original Plan: Revised
* Additional Task to Test Updated API Endpoints:
    - Test the updated API endpoints, including pagination and commenting system, thoroughly to ensure correct functionality and error handling.

**Step 7: Implement Commenting System**

* Original Plan: New Task
* Additional Tasks to Implement User Authentication for Commenting:
    - Implement user authentication for commenting.
    - Test the commenting system thoroughly to ensure it meets all requirements and refine it as needed.

**Step 8: Implement User Roles and Permissions**

* Original Plan: New Task
* Additional Tasks to Implement User Roles and Permissions System:
    - Implement user roles and permissions system.
    - Test the user roles and permissions system thoroughly to ensure it meets all requirements and refine it as needed.

**Step 9: Test and Refine API**

* Original Plan: New Task
* Additional Task to Monitor API Deployment:
    - Deploy and monitor the API to ensure its performance, scalability, and security.

**Step 10: Deploy and Monitor API**

* New Task:
    - Deploy the API using a cloud provider or containerized platform (e.g., Docker).
    - Monitor the API's performance and address any issues promptly.
  @step_count = 4
  @current_step = Refine database schema design to include additional features such as Todo item status (e.g., "in_progress", "done"), User roles and permissions, Commenting system with user authentication for comments.
  @step_result = This step refines the database schema design to include additional features such as Todo item status, User roles and permissions, and a commenting system with user authentication for comments. The resulting plan will provide a solid foundation for the project's data storage and management.

Created files:
* Revised Database Schema Design document (.docx)
* Alternative Solution Matrix table (Excel file)
  @validation = Passed.
  @files_written = Written 2 file(s) to cookbook/12_plan_and_execute/output:
  requirements.txt
  models.py
============================================================
Log: /home/gongai/.spl/logs/plan_execute-ollama-20260321-024110.log
