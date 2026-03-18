"""SPL 2.0 Optimizer: execution planning for prompts and workflows.

Extends SPL 1.0 optimizer with workflow execution planning:
- WorkflowPlan for multi-step agentic workflows
- Step-level planning for EVALUATE, WHILE, GENERATE INTO, etc.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from spl2.ast_nodes import (
    PromptStatement, SelectItem, SystemRoleCall, ContextRef,
    RagQuery, MemoryGet, Identifier, DottedName, FunctionCall,
    WorkflowStatement, ProcedureStatement,
    EvaluateStatement, WhileStatement, DoBlock,
    AssignmentStatement, GenerateIntoStatement, CommitStatement,
    RetryStatement, RaiseStatement, CallStatement, SelectIntoStatement,
)
from spl2.analyzer import AnalysisResult
from spl2.token_counter import TokenCounter


# ================================================================
# SPL 1.0 Execution Plan (for PROMPT statements) — unchanged
# ================================================================

@dataclass
class ExecutionStep:
    """A single step in the execution plan."""
    operation: str
    source: str
    alias: str
    estimated_tokens: int = 0
    limit_tokens: int | None = None
    allocated_tokens: int = 0
    compressed: bool = False
    compression_ratio: float = 1.0
    cache_status: str = "n/a"
    priority: int = 0
    cte_stmt: object = None


@dataclass
class ExecutionPlan:
    """Optimized execution plan for a PROMPT statement."""
    prompt_name: str
    model: str | None
    total_budget: int | None
    steps: list[ExecutionStep] = field(default_factory=list)
    output_budget: int = 0
    total_input_tokens: int = 0
    buffer_tokens: int = 0
    estimated_cost: float | None = None
    optimizations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


# ================================================================
# SPL 2.0 Workflow Plan
# ================================================================

@dataclass
class WorkflowStep:
    """A single step in a workflow execution plan."""
    step_type: str  # "assign", "generate", "evaluate", "while", "commit", "retry", "raise", "call", "select"
    description: str
    estimated_llm_calls: int = 0
    estimated_tokens: int = 0
    substeps: list[WorkflowStep] = field(default_factory=list)
    # For evaluate: branches
    branches: list[WorkflowBranch] = field(default_factory=list)
    # For exception handlers
    exception_handlers: list[WorkflowStep] = field(default_factory=list)


@dataclass
class WorkflowBranch:
    """A branch in an EVALUATE statement."""
    condition: str
    condition_type: str  # "semantic" or "deterministic"
    steps: list[WorkflowStep] = field(default_factory=list)


@dataclass
class WorkflowPlan:
    """Execution plan for a WORKFLOW statement."""
    workflow_name: str
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    steps: list[WorkflowStep] = field(default_factory=list)
    exception_handlers: list[WorkflowStep] = field(default_factory=list)
    total_estimated_llm_calls: int = 0
    total_estimated_tokens: int = 0
    security: dict | None = None
    accounting: dict | None = None


class Optimizer:
    """Optimize SPL 2.0 queries and workflows for execution."""

    def optimize(self, analysis: AnalysisResult) -> list[ExecutionPlan | WorkflowPlan]:
        """Generate execution plans for all statements."""
        plans = []
        for stmt in analysis.ast.statements:
            if isinstance(stmt, PromptStatement):
                plans.append(self._optimize_prompt(stmt))
            elif isinstance(stmt, WorkflowStatement):
                plans.append(self._optimize_workflow(stmt))
            elif isinstance(stmt, ProcedureStatement):
                plans.append(self._optimize_procedure(stmt))
        return plans

    def optimize_single(self, stmt: PromptStatement) -> ExecutionPlan:
        """Optimize a single prompt statement."""
        return self._optimize_prompt(stmt)

    # ================================================================
    # PROMPT Optimization (SPL 1.0 — unchanged)
    # ================================================================

    def _optimize_prompt(self, stmt: PromptStatement) -> ExecutionPlan:
        counter = TokenCounter(stmt.model)
        plan = ExecutionPlan(
            prompt_name=stmt.name,
            model=stmt.model,
            total_budget=stmt.budget,
        )

        for item in stmt.select_items:
            step = self._create_step(item)
            plan.steps.append(step)

        for cte in stmt.ctes:
            step = ExecutionStep(
                operation="cte",
                source=f"CTE: {cte.name}",
                alias=cte.name,
                estimated_tokens=cte.limit_tokens or 500,
                limit_tokens=cte.limit_tokens,
                allocated_tokens=cte.limit_tokens or 500,
                priority=1,
                cte_stmt=cte.nested_prompt,
            )
            plan.steps.append(step)

        if stmt.generate_clause and stmt.generate_clause.output_budget:
            plan.output_budget = stmt.generate_clause.output_budget
        elif stmt.budget:
            plan.output_budget = int(stmt.budget * 0.4)
        else:
            plan.output_budget = 4096

        if stmt.budget:
            self._allocate_tokens(plan, stmt.budget, counter)
        else:
            for step in plan.steps:
                step.allocated_tokens = step.limit_tokens or step.estimated_tokens

        plan.steps.sort(key=lambda s: s.priority)
        plan.total_input_tokens = sum(s.allocated_tokens for s in plan.steps)
        plan.buffer_tokens = max(0,
            (stmt.budget or 0) - plan.total_input_tokens - plan.output_budget
        )
        plan.estimated_cost = counter.estimate_cost(
            plan.total_input_tokens, plan.output_budget
        )
        return plan

    def _create_step(self, item: SelectItem) -> ExecutionStep:
        expr = item.expression
        alias = item.alias or self._infer_alias(expr)

        if isinstance(expr, SystemRoleCall):
            estimated = max(20, len(expr.description) // 4)
            return ExecutionStep(
                operation="system_role",
                source=f'system_role("{expr.description[:40]}...")',
                alias=alias,
                estimated_tokens=estimated,
                limit_tokens=item.limit_tokens,
                allocated_tokens=item.limit_tokens or estimated,
                priority=0,
            )
        elif isinstance(expr, ContextRef):
            estimated = item.limit_tokens or 1000
            return ExecutionStep(
                operation="load_context",
                source=f"context.{expr.field_name}",
                alias=alias,
                estimated_tokens=estimated,
                limit_tokens=item.limit_tokens,
                allocated_tokens=item.limit_tokens or estimated,
                priority=3,
            )
        elif isinstance(expr, RagQuery):
            top_k = expr.top_k or 5
            estimated = item.limit_tokens or top_k * 500
            return ExecutionStep(
                operation="rag_query",
                source=f"rag.query(top_k={top_k})",
                alias=alias,
                estimated_tokens=estimated,
                limit_tokens=item.limit_tokens,
                allocated_tokens=item.limit_tokens or estimated,
                cache_status="miss",
                priority=2,
            )
        elif isinstance(expr, MemoryGet):
            estimated = item.limit_tokens or 200
            return ExecutionStep(
                operation="memory_get",
                source=f'memory.get("{expr.key}")',
                alias=alias,
                estimated_tokens=estimated,
                limit_tokens=item.limit_tokens,
                allocated_tokens=item.limit_tokens or estimated,
                priority=1,
            )
        else:
            estimated = item.limit_tokens or 500
            return ExecutionStep(
                operation="load_context",
                source=str(type(expr).__name__),
                alias=alias,
                estimated_tokens=estimated,
                limit_tokens=item.limit_tokens,
                allocated_tokens=item.limit_tokens or estimated,
                priority=3,
            )

    def _allocate_tokens(self, plan: ExecutionPlan, budget: int, counter: TokenCounter):
        available = budget - plan.output_budget
        total_allocated = 0
        unlimited_steps: list[ExecutionStep] = []

        for step in plan.steps:
            if step.limit_tokens is not None:
                step.allocated_tokens = min(step.limit_tokens, step.estimated_tokens)
                total_allocated += step.allocated_tokens
            else:
                unlimited_steps.append(step)

        remaining = available - total_allocated
        if unlimited_steps and remaining > 0:
            per_step = remaining // len(unlimited_steps)
            for step in unlimited_steps:
                step.allocated_tokens = min(per_step, step.estimated_tokens)
                total_allocated += step.allocated_tokens

        if total_allocated > available:
            plan.optimizations.append("Budget exceeded, applying proportional compression")
            overflow = total_allocated - available
            sorted_steps = sorted(plan.steps, key=lambda s: s.allocated_tokens, reverse=True)
            for step in sorted_steps:
                if overflow <= 0:
                    break
                if step.operation == "system_role":
                    continue
                reduction = min(step.allocated_tokens // 2, overflow)
                step.allocated_tokens -= reduction
                step.compressed = True
                step.compression_ratio = step.allocated_tokens / max(step.estimated_tokens, 1)
                overflow -= reduction
                plan.optimizations.append(
                    f"Compressed {step.alias}: {step.estimated_tokens} -> {step.allocated_tokens} tokens "
                    f"({step.compression_ratio:.0%})"
                )

    def _infer_alias(self, expr) -> str:
        if isinstance(expr, SystemRoleCall):
            return "__system_role__"
        elif isinstance(expr, ContextRef):
            return expr.field_name
        elif isinstance(expr, RagQuery):
            return "rag_results"
        elif isinstance(expr, MemoryGet):
            return expr.key
        elif isinstance(expr, Identifier):
            return expr.name
        elif isinstance(expr, DottedName):
            return expr.parts[-1]
        elif isinstance(expr, FunctionCall):
            return expr.name
        return "unnamed"

    # ================================================================
    # WORKFLOW Optimization (SPL 2.0 — new)
    # ================================================================

    def _optimize_workflow(self, stmt: WorkflowStatement) -> WorkflowPlan:
        """Plan execution of a WORKFLOW statement."""
        plan = WorkflowPlan(
            workflow_name=stmt.name,
            inputs=[p.name for p in stmt.inputs],
            outputs=[p.name for p in stmt.outputs],
            security=stmt.security,
            accounting=stmt.accounting,
        )

        plan.steps = self._plan_body(stmt.body)
        plan.exception_handlers = self._plan_exception_handlers(stmt.exception_handlers)

        # Estimate totals
        plan.total_estimated_llm_calls = self._count_llm_calls(plan.steps)
        plan.total_estimated_tokens = self._estimate_total_tokens(plan.steps)

        return plan

    def _optimize_procedure(self, stmt: ProcedureStatement) -> WorkflowPlan:
        """Plan execution of a PROCEDURE statement."""
        plan = WorkflowPlan(
            workflow_name=stmt.name,
            inputs=[p.name for p in stmt.parameters],
            outputs=[stmt.return_type] if stmt.return_type else [],
            security=stmt.security,
            accounting=stmt.accounting,
        )

        plan.steps = self._plan_body(stmt.body)
        plan.exception_handlers = self._plan_exception_handlers(stmt.exception_handlers)
        plan.total_estimated_llm_calls = self._count_llm_calls(plan.steps)
        plan.total_estimated_tokens = self._estimate_total_tokens(plan.steps)

        return plan

    def _plan_body(self, stmts: list) -> list[WorkflowStep]:
        """Plan a list of body statements."""
        steps = []
        for stmt in stmts:
            step = self._plan_statement(stmt)
            if step:
                steps.append(step)
        return steps

    def _plan_statement(self, stmt) -> WorkflowStep | None:
        """Plan a single body statement."""
        if isinstance(stmt, AssignmentStatement):
            return WorkflowStep(
                step_type="assign",
                description=f"@{stmt.variable} := ...",
            )
        elif isinstance(stmt, GenerateIntoStatement):
            target = f" INTO @{stmt.target_variable}" if stmt.target_variable else ""
            return WorkflowStep(
                step_type="generate",
                description=f"GENERATE {stmt.generate_clause.function_name}(...){target}",
                estimated_llm_calls=1,
                estimated_tokens=stmt.generate_clause.output_budget or 1000,
            )
        elif isinstance(stmt, EvaluateStatement):
            from spl2.ast_nodes import SemanticCondition, ComparisonCondition
            branches = []
            for wc in stmt.when_clauses:
                cond = wc.condition
                if isinstance(cond, SemanticCondition):
                    cond_str = f"'{cond.semantic_value}'"
                    cond_type = "semantic"
                elif isinstance(cond, ComparisonCondition):
                    cond_str = f"{cond.operator} ..."
                    cond_type = "deterministic"
                else:
                    cond_str = "..."
                    cond_type = "unknown"
                branches.append(WorkflowBranch(
                    condition=cond_str,
                    condition_type=cond_type,
                    steps=self._plan_body(wc.statements),
                ))
            # Semantic evaluation needs an LLM call
            has_semantic = any(b.condition_type == "semantic" for b in branches)
            return WorkflowStep(
                step_type="evaluate",
                description="EVALUATE ...",
                estimated_llm_calls=1 if has_semantic else 0,
                branches=branches,
            )
        elif isinstance(stmt, WhileStatement):
            return WorkflowStep(
                step_type="while",
                description="WHILE ... DO ... END",
                substeps=self._plan_body(stmt.body),
                estimated_llm_calls=len([s for s in stmt.body
                                         if isinstance(s, GenerateIntoStatement)]) * 5,
            )
        elif isinstance(stmt, CommitStatement):
            return WorkflowStep(
                step_type="commit",
                description="COMMIT ...",
            )
        elif isinstance(stmt, RetryStatement):
            return WorkflowStep(
                step_type="retry",
                description="RETRY",
                estimated_llm_calls=1,
            )
        elif isinstance(stmt, RaiseStatement):
            return WorkflowStep(
                step_type="raise",
                description=f"RAISE {stmt.exception_type}",
            )
        elif isinstance(stmt, CallStatement):
            return WorkflowStep(
                step_type="call",
                description=f"CALL {stmt.procedure_name}(...)",
                estimated_llm_calls=1,
            )
        elif isinstance(stmt, SelectIntoStatement):
            return WorkflowStep(
                step_type="select",
                description="SELECT ... INTO ...",
            )
        elif isinstance(stmt, DoBlock):
            return WorkflowStep(
                step_type="do_block",
                description="DO ... END",
                substeps=self._plan_body(stmt.statements),
                exception_handlers=self._plan_exception_handlers(stmt.exception_handlers),
            )
        return None

    def _plan_exception_handlers(self, handlers: list) -> list[WorkflowStep]:
        """Plan exception handler blocks."""
        steps = []
        for handler in handlers:
            steps.append(WorkflowStep(
                step_type="exception_handler",
                description=f"WHEN {handler.exception_type} THEN ...",
                substeps=self._plan_body(handler.statements),
            ))
        return steps

    def _count_llm_calls(self, steps: list[WorkflowStep]) -> int:
        """Estimate total LLM calls across all steps."""
        total = 0
        for step in steps:
            total += step.estimated_llm_calls
            total += self._count_llm_calls(step.substeps)
            for branch in step.branches:
                total += self._count_llm_calls(branch.steps)
        return total

    def _estimate_total_tokens(self, steps: list[WorkflowStep]) -> int:
        """Estimate total tokens across all steps."""
        total = 0
        for step in steps:
            total += step.estimated_tokens
            total += self._estimate_total_tokens(step.substeps)
            for branch in step.branches:
                total += self._estimate_total_tokens(branch.steps)
        return total
