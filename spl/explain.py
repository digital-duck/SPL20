"""SPL 2.0 EXPLAIN: render execution plans in human-readable format.

Supports both PROMPT execution plans and WORKFLOW execution plans.
"""

from spl.optimizer import ExecutionPlan, WorkflowPlan, WorkflowStep


def explain_plan(plan: ExecutionPlan | WorkflowPlan) -> str:
    """Render an execution plan as a formatted string."""
    if isinstance(plan, WorkflowPlan):
        return _explain_workflow(plan)
    return _explain_prompt(plan)


def explain_plans(plans: list[ExecutionPlan | WorkflowPlan]) -> str:
    """Render multiple execution plans."""
    return '\n\n'.join(explain_plan(p) for p in plans)


# ================================================================
# PROMPT Plan Rendering (SPL 1.0 — unchanged)
# ================================================================

def _explain_prompt(plan: ExecutionPlan) -> str:
    lines: list[str] = []

    lines.append(f"Execution Plan for: {plan.prompt_name}")
    lines.append("=" * 60)

    budget_str = f"{plan.total_budget:,} tokens" if plan.total_budget else "unlimited"
    model_str = plan.model or "default"
    lines.append(f"Budget: {budget_str} | Model: {model_str}")
    lines.append("")

    lines.append("Token Allocation:")

    total_all = plan.total_input_tokens + plan.output_budget + plan.buffer_tokens
    if total_all == 0:
        total_all = 1

    for i, step in enumerate(plan.steps):
        is_last_step = (i == len(plan.steps) - 1) and plan.output_budget == 0
        prefix = "+-- " if not is_last_step else "\\-- "

        pct = step.allocated_tokens / total_all * 100
        annotation = _step_annotation(step)

        line = (
            f"{prefix}{step.alias:<25s} "
            f"{step.allocated_tokens:>6,} tokens  "
            f"({pct:>5.1f}%)"
        )
        if annotation:
            line += f"  [{annotation}]"
        lines.append(line)

    if plan.output_budget:
        pct = plan.output_budget / total_all * 100
        lines.append(f"+-- {'Output Budget':<25s} {plan.output_budget:>6,} tokens  ({pct:>5.1f}%)")

    if plan.buffer_tokens > 0:
        pct = plan.buffer_tokens / total_all * 100
        lines.append(f"\\-- {'Buffer':<25s} {plan.buffer_tokens:>6,} tokens  ({pct:>5.1f}%)")

    lines.append(f"{'':>4s}{'':->36s}")

    if plan.total_budget:
        usage_pct = (plan.total_input_tokens + plan.output_budget) / plan.total_budget * 100
        lines.append(
            f"{'Total':<29s} {plan.total_input_tokens + plan.output_budget:>6,} / "
            f"{plan.total_budget:,} tokens ({usage_pct:.1f}%)"
        )
    else:
        lines.append(
            f"{'Total':<29s} {plan.total_input_tokens + plan.output_budget:>6,} tokens"
        )

    lines.append("")

    if plan.estimated_cost is not None:
        lines.append(f"Estimated Cost: ${plan.estimated_cost:.4f}")

    if plan.optimizations:
        lines.append("")
        lines.append("Optimizations Applied:")
        for opt in plan.optimizations:
            lines.append(f"  * {opt}")

    if plan.warnings:
        lines.append("")
        lines.append("Warnings:")
        for warn in plan.warnings:
            lines.append(f"  ! {warn}")

    return '\n'.join(lines)


def _step_annotation(step) -> str:
    parts = []
    if step.compressed:
        ratio_pct = (1.0 - step.compression_ratio) * 100
        parts.append(f"compressed {ratio_pct:.0f}%")
    if step.cache_status == "hit":
        parts.append("cache HIT")
    elif step.cache_status == "miss":
        parts.append("cache MISS")
    if step.operation == "memory_get":
        parts.append("from memory")
    return ", ".join(parts)


# ================================================================
# WORKFLOW Plan Rendering (SPL 2.0 — new)
# ================================================================

def _explain_workflow(plan: WorkflowPlan) -> str:
    lines: list[str] = []

    lines.append(f"Workflow Plan for: {plan.workflow_name}")
    lines.append("=" * 60)

    if plan.inputs:
        lines.append(f"Inputs:  {', '.join('@' + i for i in plan.inputs)}")
    if plan.outputs:
        lines.append(f"Outputs: {', '.join('@' + o for o in plan.outputs)}")

    if plan.security:
        lines.append(f"Security: {plan.security}")
    if plan.accounting:
        lines.append(f"Accounting: {plan.accounting}")

    lines.append(f"Estimated LLM Calls: {plan.total_estimated_llm_calls}")
    if plan.total_estimated_tokens > 0:
        lines.append(f"Estimated Tokens: {plan.total_estimated_tokens:,}")
    lines.append("")

    lines.append("Execution Steps:")
    for step in plan.steps:
        _render_workflow_step(step, lines, indent=1)

    if plan.exception_handlers:
        lines.append("")
        lines.append("Exception Handlers:")
        for handler in plan.exception_handlers:
            _render_workflow_step(handler, lines, indent=1)

    return '\n'.join(lines)


def _render_workflow_step(step: WorkflowStep, lines: list[str], indent: int = 0):
    """Recursively render a workflow step."""
    prefix = "  " * indent
    icon = _step_icon(step.step_type)
    detail = ""
    if step.estimated_llm_calls > 0:
        detail = f"  [{step.estimated_llm_calls} LLM call(s)]"

    lines.append(f"{prefix}{icon} {step.description}{detail}")

    # Render branches (EVALUATE)
    for branch in step.branches:
        ctype = "semantic" if branch.condition_type == "semantic" else "determ."
        lines.append(f"{prefix}  WHEN {branch.condition} ({ctype}):")
        for substep in branch.steps:
            _render_workflow_step(substep, lines, indent + 2)

    # Render substeps (WHILE body, DO block, exception handlers)
    for substep in step.substeps:
        _render_workflow_step(substep, lines, indent + 1)

    # Render exception handlers
    for handler in step.exception_handlers:
        _render_workflow_step(handler, lines, indent + 1)


def _step_icon(step_type: str) -> str:
    icons = {
        "assign": ":=",
        "generate": ">>",
        "evaluate": "??",
        "while": "~~",
        "commit": "OK",
        "retry": "<-",
        "raise": "!!",
        "call": "->",
        "select": "<>",
        "do_block": "{}",
        "exception_handler": "EX",
    }
    return icons.get(step_type, "--")
