
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

-- Execute a step and produce working code
CREATE FUNCTION execute_step(current_step TEXT, prior_results TEXT) RETURNS TEXT AS $$
You are a senior software engineer. Implement the following step completely.

Step to implement:
{current_step}

Prior work already completed:
{prior_results}

Requirements:
- Write complete, production-quality code — no placeholders, no TODOs.
- Use markdown code blocks. Start each block with a filename comment as the FIRST line:

  ```python
  # filename: app/main.py
  ...code...
  ```

- Each file should be its own fenced code block.
- Include error handling, type hints (Python), and brief inline comments.
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

-- Synthesize all step outputs into a final report
CREATE FUNCTION synthesize(task TEXT, results TEXT) RETURNS TEXT AS $$
Synthesize a final implementation report for this task.

Task: {task}

Completed work:
{results}

Write a brief summary (3–5 sentences) describing what was built, key design decisions,
and how to run the project. Then include all generated code blocks exactly as-is.
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

