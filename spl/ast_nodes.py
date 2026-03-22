"""SPL 2.0 Abstract Syntax Tree node definitions.

Extends SPL 1.0 AST with nodes for agentic workflow orchestration:
- WorkflowStatement, ProcedureStatement
- DoBlock, ExceptionHandler
- EvaluateStatement, WhenClause, SemanticCondition
- WhileStatement
- CommitStatement, RetryStatement, RaiseStatement
- AssignmentStatement
- GenerateInto (GENERATE ... INTO @var)
- CallStatement (CALL procedure(...))
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Union


# === Expression Nodes (SPL 1.0 — unchanged) ===

@dataclass
class Expression:
    """Base class for all expressions."""
    pass


@dataclass
class Literal(Expression):
    """String, integer, or float literal."""
    value: str | int | float
    literal_type: str  # "string", "integer", "float"


@dataclass
class Identifier(Expression):
    """Simple identifier (e.g., 'profile')."""
    name: str


@dataclass
class DottedName(Expression):
    """Dotted identifier (e.g., 'context.user_profile', 'docs.relevance')."""
    parts: list[str]

    @property
    def full_name(self) -> str:
        return '.'.join(self.parts)


@dataclass
class ParamRef(Expression):
    """Parameter reference (e.g., '@user_data')."""
    name: str


@dataclass
class FunctionCall(Expression):
    """Function call (e.g., 'summarize(text, 200)')."""
    name: str
    arguments: list[Expression] = field(default_factory=list)


@dataclass
class BinaryOp(Expression):
    """Binary operation (e.g., 'a + b')."""
    left: Expression
    op: str  # "+", "-"
    right: Expression


@dataclass
class NamedArg(Expression):
    """Named argument in function call (e.g., 'top_k=5')."""
    name: str
    value: Expression


# === Source Expressions (SPL 1.0 — unchanged) ===

@dataclass
class SystemRoleCall(Expression):
    """system_role("description")."""
    description: str


@dataclass
class ContextRef(Expression):
    """context.<field> reference."""
    field_name: str


@dataclass
class RagQuery(Expression):
    """rag.query("search text", top_k=5)."""
    query_text: Expression
    top_k: int | None = None


@dataclass
class MemoryGet(Expression):
    """memory.get("key")."""
    key: str


# === Clause Nodes (SPL 1.0 — unchanged) ===

@dataclass
class SelectItem:
    """Single item in a SELECT clause."""
    expression: Expression
    alias: str | None = None
    limit_tokens: int | None = None


@dataclass
class Condition:
    """Single condition in a WHERE clause (deterministic comparison)."""
    left: Expression
    operator: str  # "=", "!=", ">", "<", ">=", "<=", "IN"
    right: Expression


@dataclass
class WhereClause:
    """WHERE clause with conditions joined by AND/OR."""
    conditions: list[Condition] = field(default_factory=list)
    conjunctions: list[str] = field(default_factory=list)  # "AND", "OR" between conditions


@dataclass
class OrderByItem:
    """Single item in ORDER BY."""
    expression: Expression
    direction: str = "ASC"  # "ASC" or "DESC"


@dataclass
class GenerateClause:
    """GENERATE function(args) WITH options."""
    function_name: str
    arguments: list[Expression] = field(default_factory=list)
    output_budget: int | None = None
    temperature: float | None = None
    output_format: str | None = None
    schema: str | None = None
    model: str | None = None


@dataclass
class StoreClause:
    """STORE RESULT IN memory.<key>."""
    key: str


@dataclass
class FromClause:
    """FROM source AS alias."""
    source: Expression
    alias: str | None = None


# === CTE (SPL 1.0 — unchanged) ===

@dataclass
class CTEClause:
    """WITH <name> AS (...) common table expression."""
    name: str
    select_items: list[SelectItem] = field(default_factory=list)
    from_clause: FromClause | None = None
    where_clause: WhereClause | None = None
    limit_tokens: int | None = None
    nested_prompt: PromptStatement | None = None


# === SPL 1.0 Top-Level Statements (unchanged) ===

@dataclass
class PromptStatement:
    """PROMPT <name> WITH BUDGET ... SELECT ... GENERATE ..."""
    name: str
    budget: int | None = None
    model: str | None = None
    cache_duration: str | None = None
    version: str | None = None
    ctes: list[CTEClause] = field(default_factory=list)
    select_items: list[SelectItem] = field(default_factory=list)
    where_clause: WhereClause | None = None
    order_by: list[OrderByItem] | None = None
    generate_clause: GenerateClause | None = None
    store_clause: StoreClause | None = None
    on_grid: str | None = None
    min_vram_gb: float | None = None


@dataclass
class Parameter:
    """Function/workflow parameter definition."""
    name: str
    param_type: str | None = None
    default_value: Expression | None = None


@dataclass
class CreateFunctionStatement:
    """CREATE FUNCTION <name>(...) RETURNS <type> AS $$ ... $$"""
    name: str
    parameters: list[Parameter] = field(default_factory=list)
    return_type: str = "text"
    body: str = ""


@dataclass
class ExplainStatement:
    """EXPLAIN PROMPT <name>."""
    prompt_name: str


@dataclass
class ExecuteStatement:
    """EXECUTE PROMPT <name> WITH PARAMS (...)."""
    prompt_name: str
    params: dict[str, Expression] = field(default_factory=dict)


# ===========================================================
# === SPL 2.0 New Nodes ===
# ===========================================================

@dataclass
class SemanticCondition:
    """Semantic condition evaluated by LLM, e.g., 'coherent', 'complete'."""
    semantic_value: str


@dataclass
class WhenClause:
    """WHEN <condition> THEN <statements>"""
    condition: Condition | SemanticCondition | ComparisonCondition
    statements: list = field(default_factory=list)


@dataclass
class ComparisonCondition:
    """Comparison condition in EVALUATE context (e.g., > 0.8, <= 0.5)."""
    operator: str
    right: Expression


@dataclass
class ExceptionHandler:
    """WHEN <exception_type> THEN <statements>"""
    exception_type: str  # e.g., "HallucinationDetected", "OTHERS"
    statements: list = field(default_factory=list)


@dataclass
class DoBlock:
    """DO <statements> END or DO <statements> EXCEPTION ... END"""
    statements: list = field(default_factory=list)
    exception_handlers: list[ExceptionHandler] = field(default_factory=list)


@dataclass
class EvaluateStatement:
    """EVALUATE <expr> WHEN <condition> THEN <statements> ... END"""
    expression: Expression
    when_clauses: list[WhenClause] = field(default_factory=list)
    otherwise_statements: list = field(default_factory=list)


@dataclass
class WhileStatement:
    """WHILE <condition> DO <statements> END"""
    condition: Condition | SemanticCondition | Expression
    body: list = field(default_factory=list)
    max_iterations: int | None = None


@dataclass
class CommitStatement:
    """COMMIT <expr> WITH status='...'"""
    expression: Expression
    options: dict[str, Expression] = field(default_factory=dict)


@dataclass
class RetryStatement:
    """RETRY WITH fallback options"""
    options: dict[str, Expression] = field(default_factory=dict)


@dataclass
class RaiseStatement:
    """RAISE <exception_type> [message]"""
    exception_type: str
    message: str | None = None


@dataclass
class AssignmentStatement:
    """@var := expr"""
    variable: str
    expression: Expression


@dataclass
class GenerateIntoStatement:
    """GENERATE function(args) WITH options INTO @var"""
    generate_clause: GenerateClause
    target_variable: str


@dataclass
class CallStatement:
    """CALL procedure(args) INTO @var"""
    procedure_name: str
    arguments: list[Expression] = field(default_factory=list)
    target_variable: str | None = None


@dataclass
class SelectIntoStatement:
    """SELECT ... FROM ... INTO @var (used inside workflows), optional CTE block"""
    select_items: list[SelectItem] = field(default_factory=list)
    from_clause: FromClause | None = None
    where_clause: WhereClause | None = None
    target_variable: str | None = None           # single-var (backward compat)
    target_variables: list[str] = field(default_factory=list)  # multi-var INTO
    ctes: list = field(default_factory=list)     # list[CTEClause]


@dataclass
class WorkflowStatement:
    """WORKFLOW <name> INPUT ... OUTPUT ... DO ... END"""
    name: str
    inputs: list[Parameter] = field(default_factory=list)
    outputs: list[Parameter] = field(default_factory=list)
    security: dict | None = None
    accounting: dict | None = None
    labels: dict | None = None
    body: list = field(default_factory=list)
    exception_handlers: list[ExceptionHandler] = field(default_factory=list)


@dataclass
class ProcedureStatement:
    """PROCEDURE <name>(...) RETURNS type DO ... END"""
    name: str
    parameters: list[Parameter] = field(default_factory=list)
    return_type: str | None = None
    security: dict | None = None
    accounting: dict | None = None
    body: list = field(default_factory=list)
    exception_handlers: list[ExceptionHandler] = field(default_factory=list)


# === Top-Level Program ===

# Union of all statement types that can appear at the top level
Statement = Union[
    PromptStatement,
    CreateFunctionStatement,
    ExplainStatement,
    ExecuteStatement,
    WorkflowStatement,
    ProcedureStatement,
    EvaluateStatement,
    WhileStatement,
    DoBlock,
    CommitStatement,
    RetryStatement,
    RaiseStatement,
    AssignmentStatement,
    GenerateIntoStatement,
    CallStatement,
    SelectIntoStatement,
]


@dataclass
class Program:
    """Top-level program node containing a list of statements."""
    statements: list[Statement] = field(default_factory=list)
