"""SPL 2.0 Intermediate Representation: JSON serialization of AST and plans.

Produces a portable JSON format suitable for:
- Momagrid execution runtime
- Plan visualization tools
- Cross-language interop
"""

from __future__ import annotations

from spl.ast_nodes import (
    Program, PromptStatement, WorkflowStatement, ProcedureStatement,
    CreateFunctionStatement, ExplainStatement, ExecuteStatement,
    SelectItem, SystemRoleCall, ContextRef, RagQuery, MemoryGet,
    Identifier, Literal, ParamRef, BinaryOp, FunctionCall, DottedName,
    EvaluateStatement, WhileStatement, DoBlock,
    AssignmentStatement, GenerateIntoStatement, CommitStatement,
    RetryStatement, RaiseStatement, CallStatement, SelectIntoStatement,
    SemanticCondition, ComparisonCondition, Condition,
    ExceptionHandler, WhenClause,
)
from spl.optimizer import (
    ExecutionPlan, WorkflowPlan, WorkflowStep,
)


# ================================================================
# AST → JSON
# ================================================================

def ast_to_json(program: Program) -> dict:
    """Serialize a full AST program to a JSON-compatible dict."""
    return {
        "type": "Program",
        "statements": [_stmt_to_json(s) for s in program.statements],
    }


def _stmt_to_json(stmt) -> dict:
    if isinstance(stmt, PromptStatement):
        return _prompt_to_json(stmt)
    elif isinstance(stmt, WorkflowStatement):
        return _workflow_to_json(stmt)
    elif isinstance(stmt, ProcedureStatement):
        return _procedure_to_json(stmt)
    elif isinstance(stmt, CreateFunctionStatement):
        return {
            "type": "CreateFunction",
            "name": stmt.name,
            "parameters": [{"name": p.name, "type": p.param_type} for p in stmt.parameters],
            "return_type": stmt.return_type,
            "body": stmt.body,
        }
    elif isinstance(stmt, ExplainStatement):
        return {
            "type": "Explain",
            "prompt_name": stmt.prompt_name,
        }
    elif isinstance(stmt, ExecuteStatement):
        return {
            "type": "Execute",
            "prompt_name": stmt.prompt_name,
            "params": {k: _expr_to_json(v) for k, v in stmt.params.items()},
        }
    return {"type": type(stmt).__name__}


def _prompt_to_json(stmt: PromptStatement) -> dict:
    result: dict = {
        "type": "Prompt",
        "name": stmt.name,
        "model": stmt.model,
        "budget": stmt.budget,
        "select_items": [_select_item_to_json(si) for si in stmt.select_items],
    }
    if stmt.ctes:
        result["ctes"] = [{
            "name": c.name,
            "limit_tokens": c.limit_tokens,
            "nested_prompt": _stmt_to_json(c.nested_prompt) if c.nested_prompt else None,
        } for c in stmt.ctes]
    if stmt.generate_clause:
        gc = stmt.generate_clause
        result["generate"] = {
            "function": gc.function_name,
            "arguments": [_expr_to_json(a) for a in gc.arguments],
            "output_budget": gc.output_budget,
            "temperature": gc.temperature,
            "format": gc.output_format,
        }
    if stmt.store_clause:
        result["store"] = {"key": stmt.store_clause.key}
    return result


def _workflow_to_json(stmt: WorkflowStatement) -> dict:
    return {
        "type": "Workflow",
        "name": stmt.name,
        "inputs": [{"name": p.name, "type": p.param_type, "default": _expr_to_json(p.default_value) if p.default_value else None} for p in stmt.inputs],
        "outputs": [{"name": p.name, "type": p.param_type} for p in stmt.outputs],
        "security": stmt.security,
        "accounting": stmt.accounting,
        "labels": stmt.labels,
        "body": [_body_stmt_to_json(s) for s in stmt.body],
        "exception_handlers": [_handler_to_json(h) for h in stmt.exception_handlers],
    }


def _procedure_to_json(stmt: ProcedureStatement) -> dict:
    return {
        "type": "Procedure",
        "name": stmt.name,
        "parameters": [{"name": p.name, "type": p.param_type, "default": _expr_to_json(p.default_value) if p.default_value else None} for p in stmt.parameters],
        "return_type": stmt.return_type,
        "security": stmt.security,
        "accounting": stmt.accounting,
        "body": [_body_stmt_to_json(s) for s in stmt.body],
        "exception_handlers": [_handler_to_json(h) for h in stmt.exception_handlers],
    }


def _body_stmt_to_json(stmt) -> dict:
    if isinstance(stmt, AssignmentStatement):
        return {
            "type": "Assignment",
            "variable": stmt.variable,
            "expression": _expr_to_json(stmt.expression),
        }
    elif isinstance(stmt, GenerateIntoStatement):
        gc = stmt.generate_clause
        return {
            "type": "GenerateInto",
            "function": gc.function_name,
            "arguments": [_expr_to_json(a) for a in gc.arguments],
            "output_budget": gc.output_budget,
            "temperature": gc.temperature,
            "target_variable": stmt.target_variable,
        }
    elif isinstance(stmt, EvaluateStatement):
        return {
            "type": "Evaluate",
            "expression": _expr_to_json(stmt.expression),
            "when_clauses": [_when_to_json(wc) for wc in stmt.when_clauses],
            "otherwise": [_body_stmt_to_json(s) for s in stmt.otherwise_statements] if stmt.otherwise_statements else None,
        }
    elif isinstance(stmt, WhileStatement):
        return {
            "type": "While",
            "condition": _condition_to_json(stmt.condition),
            "body": [_body_stmt_to_json(s) for s in stmt.body],
        }
    elif isinstance(stmt, CommitStatement):
        return {
            "type": "Commit",
            "expression": _expr_to_json(stmt.expression),
            "options": {k: _expr_to_json(v) for k, v in stmt.options.items()},
        }
    elif isinstance(stmt, RetryStatement):
        return {
            "type": "Retry",
            "options": {k: _expr_to_json(v) for k, v in stmt.options.items()},
        }
    elif isinstance(stmt, RaiseStatement):
        return {
            "type": "Raise",
            "exception_type": stmt.exception_type,
            "message": stmt.message,
        }
    elif isinstance(stmt, CallStatement):
        return {
            "type": "Call",
            "procedure": stmt.procedure_name,
            "arguments": [_expr_to_json(a) for a in stmt.arguments],
            "target_variable": stmt.target_variable,
        }
    elif isinstance(stmt, SelectIntoStatement):
        return {
            "type": "SelectInto",
            "items": [_select_item_to_json(si) for si in stmt.select_items],
            "target_variable": stmt.target_variable,
        }
    elif isinstance(stmt, DoBlock):
        return {
            "type": "DoBlock",
            "statements": [_body_stmt_to_json(s) for s in stmt.statements],
            "exception_handlers": [_handler_to_json(h) for h in stmt.exception_handlers],
        }
    return {"type": type(stmt).__name__}


def _select_item_to_json(item: SelectItem) -> dict:
    return {
        "expression": _expr_to_json(item.expression),
        "alias": item.alias,
        "limit_tokens": item.limit_tokens,
    }


def _expr_to_json(expr) -> dict:
    if isinstance(expr, Literal):
        return {"type": "Literal", "value": expr.value}
    elif isinstance(expr, Identifier):
        return {"type": "Identifier", "name": expr.name}
    elif isinstance(expr, ParamRef):
        return {"type": "ParamRef", "name": expr.name}
    elif isinstance(expr, DottedName):
        return {"type": "DottedName", "parts": expr.parts, "full_name": expr.full_name}
    elif isinstance(expr, SystemRoleCall):
        return {"type": "SystemRole", "description": expr.description}
    elif isinstance(expr, ContextRef):
        return {"type": "ContextRef", "field_name": expr.field_name}
    elif isinstance(expr, RagQuery):
        return {"type": "RagQuery", "query": expr.query, "source": expr.source, "top_k": expr.top_k}
    elif isinstance(expr, MemoryGet):
        return {"type": "MemoryGet", "key": expr.key}
    elif isinstance(expr, FunctionCall):
        return {
            "type": "FunctionCall",
            "name": expr.name,
            "arguments": [_expr_to_json(a) for a in expr.arguments],
        }
    elif isinstance(expr, BinaryOp):
        return {
            "type": "BinaryOp",
            "op": expr.op,
            "left": _expr_to_json(expr.left),
            "right": _expr_to_json(expr.right),
        }
    return {"type": type(expr).__name__, "repr": str(expr)}


def _condition_to_json(cond) -> dict:
    if isinstance(cond, SemanticCondition):
        return {"type": "SemanticCondition", "value": cond.semantic_value}
    elif isinstance(cond, ComparisonCondition):
        return {"type": "ComparisonCondition", "operator": cond.operator, "right": _expr_to_json(cond.right)}
    elif isinstance(cond, Condition):
        return {
            "type": "Condition",
            "left": _expr_to_json(cond.left),
            "operator": cond.operator,
            "right": _expr_to_json(cond.right),
        }
    return _expr_to_json(cond)


def _when_to_json(wc: WhenClause) -> dict:
    return {
        "condition": _condition_to_json(wc.condition),
        "statements": [_body_stmt_to_json(s) for s in wc.statements],
    }


def _handler_to_json(handler: ExceptionHandler) -> dict:
    return {
        "exception_type": handler.exception_type,
        "statements": [_body_stmt_to_json(s) for s in handler.statements],
    }


# ================================================================
# Plan → JSON
# ================================================================

def plan_to_json(plan: ExecutionPlan | WorkflowPlan) -> dict:
    """Serialize an execution plan to a JSON-compatible dict."""
    if isinstance(plan, WorkflowPlan):
        return _workflow_plan_to_json(plan)
    return _prompt_plan_to_json(plan)


def plans_to_json(plans: list[ExecutionPlan | WorkflowPlan]) -> list[dict]:
    """Serialize multiple plans."""
    return [plan_to_json(p) for p in plans]


def _prompt_plan_to_json(plan: ExecutionPlan) -> dict:
    return {
        "type": "PromptPlan",
        "prompt_name": plan.prompt_name,
        "model": plan.model,
        "total_budget": plan.total_budget,
        "output_budget": plan.output_budget,
        "total_input_tokens": plan.total_input_tokens,
        "buffer_tokens": plan.buffer_tokens,
        "estimated_cost": plan.estimated_cost,
        "optimizations": plan.optimizations,
        "warnings": plan.warnings,
        "steps": [{
            "operation": s.operation,
            "source": s.source,
            "alias": s.alias,
            "estimated_tokens": s.estimated_tokens,
            "limit_tokens": s.limit_tokens,
            "allocated_tokens": s.allocated_tokens,
            "compressed": s.compressed,
            "compression_ratio": s.compression_ratio,
            "cache_status": s.cache_status,
            "priority": s.priority,
        } for s in plan.steps],
    }


def _workflow_plan_to_json(plan: WorkflowPlan) -> dict:
    return {
        "type": "WorkflowPlan",
        "workflow_name": plan.workflow_name,
        "inputs": plan.inputs,
        "outputs": plan.outputs,
        "security": plan.security,
        "accounting": plan.accounting,
        "total_estimated_llm_calls": plan.total_estimated_llm_calls,
        "total_estimated_tokens": plan.total_estimated_tokens,
        "steps": [_workflow_step_to_json(s) for s in plan.steps],
        "exception_handlers": [_workflow_step_to_json(s) for s in plan.exception_handlers],
    }


def _workflow_step_to_json(step: WorkflowStep) -> dict:
    result: dict = {
        "step_type": step.step_type,
        "description": step.description,
        "estimated_llm_calls": step.estimated_llm_calls,
        "estimated_tokens": step.estimated_tokens,
    }
    if step.substeps:
        result["substeps"] = [_workflow_step_to_json(s) for s in step.substeps]
    if step.branches:
        result["branches"] = [{
            "condition": b.condition,
            "condition_type": b.condition_type,
            "steps": [_workflow_step_to_json(s) for s in b.steps],
        } for b in step.branches]
    if step.exception_handlers:
        result["exception_handlers"] = [_workflow_step_to_json(s) for s in step.exception_handlers]
    return result
