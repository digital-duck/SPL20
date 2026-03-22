"""SPL 2.0 Semantic Analyzer: validates AST for correctness.

Extends SPL 1.0 analyzer with validation for:
- Workflow/Procedure definitions
- EVALUATE condition types (semantic vs deterministic)
- Exception type validation
- Variable scope analysis for @var assignments
"""

from spl.ast_nodes import (
    Program, PromptStatement, CreateFunctionStatement, ExplainStatement,
    ExecuteStatement, SelectItem, CTEClause, GenerateClause,
    SystemRoleCall, ContextRef, RagQuery, MemoryGet, Identifier,
    DottedName, FunctionCall,
    # SPL 2.0 nodes
    WorkflowStatement, ProcedureStatement, DoBlock, ExceptionHandler,
    EvaluateStatement, WhenClause, SemanticCondition, ComparisonCondition,
    WhileStatement, CommitStatement, RetryStatement, RaiseStatement,
    AssignmentStatement, GenerateIntoStatement, CallStatement, SelectIntoStatement,
)


class AnalysisError(Exception):
    """Raised when semantic analysis finds an error."""
    pass


class AnalysisWarning:
    """Non-fatal warning from analysis."""
    def __init__(self, message: str):
        self.message = message

    def __repr__(self) -> str:
        return f"Warning: {self.message}"


# Valid exception types for EXCEPTION handlers
VALID_EXCEPTION_TYPES = {
    'HallucinationDetected',
    'RefusalToAnswer',
    'ContextLengthExceeded',
    'ModelOverloaded',
    'QualityBelowThreshold',
    'MaxIterationsReached',
    'BudgetExceeded',
    'NodeUnavailable',
    'OTHERS',
    'Others',
}

# Valid security classification levels
VALID_CLASSIFICATIONS = {'public', 'internal', 'confidential', 'restricted'}


class AnalysisResult:
    """Result of semantic analysis."""
    def __init__(self, ast: Program):
        self.ast = ast
        self.warnings: list[AnalysisWarning] = []
        self.defined_prompts: dict[str, PromptStatement] = {}
        self.defined_functions: dict[str, CreateFunctionStatement] = {}
        self.defined_workflows: dict[str, WorkflowStatement] = {}
        self.defined_procedures: dict[str, ProcedureStatement] = {}

    @property
    def is_valid(self) -> bool:
        return True  # If we got here without raising, it's valid


class Analyzer:
    """Semantic analyzer for SPL 2.0 AST."""

    def analyze(self, program: Program) -> AnalysisResult:
        """Validate the AST and return analysis result."""
        result = AnalysisResult(ast=program)

        for stmt in program.statements:
            if isinstance(stmt, CreateFunctionStatement):
                self._analyze_create_function(stmt, result)
            elif isinstance(stmt, PromptStatement):
                self._analyze_prompt(stmt, result)
            elif isinstance(stmt, ExplainStatement):
                self._analyze_explain(stmt, result)
            elif isinstance(stmt, ExecuteStatement):
                self._analyze_execute(stmt, result)
            elif isinstance(stmt, WorkflowStatement):
                self._analyze_workflow(stmt, result)
            elif isinstance(stmt, ProcedureStatement):
                self._analyze_procedure(stmt, result)

        return result

    # === SPL 1.0 Analysis (unchanged) ===

    def _analyze_create_function(self, stmt: CreateFunctionStatement, result: AnalysisResult):
        if stmt.name in result.defined_functions:
            raise AnalysisError(f"Function '{stmt.name}' already defined")
        result.defined_functions[stmt.name] = stmt

    def _analyze_prompt(self, stmt: PromptStatement, result: AnalysisResult):
        if stmt.name in result.defined_prompts:
            raise AnalysisError(f"Prompt '{stmt.name}' already defined")
        result.defined_prompts[stmt.name] = stmt

        defined_aliases: set[str] = set()

        for cte in stmt.ctes:
            if cte.name in defined_aliases:
                raise AnalysisError(f"Duplicate CTE name '{cte.name}'")
            defined_aliases.add(cte.name)
            self._validate_select_items(cte.select_items, defined_aliases, result)

        for item in stmt.select_items:
            if item.alias:
                defined_aliases.add(item.alias)

        if stmt.budget is not None:
            total_limits = 0
            for item in stmt.select_items:
                if item.limit_tokens is not None:
                    total_limits += item.limit_tokens
            for cte in stmt.ctes:
                if cte.limit_tokens is not None:
                    total_limits += cte.limit_tokens

            output_budget = 0
            if stmt.generate_clause and stmt.generate_clause.output_budget:
                output_budget = stmt.generate_clause.output_budget

            if total_limits + output_budget > stmt.budget:
                result.warnings.append(AnalysisWarning(
                    f"Sum of LIMIT clauses ({total_limits}) + output budget ({output_budget}) "
                    f"= {total_limits + output_budget} exceeds total budget ({stmt.budget}). "
                    f"Optimizer will apply compression."
                ))

        if stmt.generate_clause:
            self._validate_generate(stmt.generate_clause, defined_aliases, result)

    def _validate_select_items(self, items: list[SelectItem], aliases: set[str],
                               result: AnalysisResult):
        for item in items:
            if item.limit_tokens is not None and item.limit_tokens <= 0:
                raise AnalysisError("LIMIT tokens must be positive")

    def _validate_generate(self, gen: GenerateClause, aliases: set[str],
                           result: AnalysisResult):
        for arg in gen.arguments:
            if isinstance(arg, Identifier):
                if arg.name not in aliases:
                    result.warnings.append(AnalysisWarning(
                        f"GENERATE argument '{arg.name}' is not a defined alias. "
                        f"Available: {', '.join(sorted(aliases))}"
                    ))

        if gen.temperature is not None:
            if gen.temperature < 0 or gen.temperature > 2.0:
                raise AnalysisError(
                    f"Temperature must be between 0 and 2.0, got {gen.temperature}"
                )

        if gen.output_budget is not None and gen.output_budget <= 0:
            raise AnalysisError("OUTPUT BUDGET must be positive")

    def _analyze_explain(self, stmt: ExplainStatement, result: AnalysisResult):
        pass

    def _analyze_execute(self, stmt: ExecuteStatement, result: AnalysisResult):
        pass

    # === SPL 2.0 Analysis ===

    def _analyze_workflow(self, stmt: WorkflowStatement, result: AnalysisResult):
        """Validate a WORKFLOW statement."""
        if stmt.name in result.defined_workflows:
            raise AnalysisError(f"Workflow '{stmt.name}' already defined")
        result.defined_workflows[stmt.name] = stmt

        # Validate security metadata
        if stmt.security:
            self._validate_security(stmt.security, result)

        # Validate accounting metadata
        if stmt.accounting:
            self._validate_accounting(stmt.accounting, result)

        # Validate body statements
        scope = set()
        for param in stmt.inputs:
            scope.add(param.name)
        for param in stmt.outputs:
            scope.add(param.name)

        self._validate_body(stmt.body, scope, result)
        self._validate_exception_handlers(stmt.exception_handlers, result)

    def _analyze_procedure(self, stmt: ProcedureStatement, result: AnalysisResult):
        """Validate a PROCEDURE statement."""
        if stmt.name in result.defined_procedures:
            raise AnalysisError(f"Procedure '{stmt.name}' already defined")
        result.defined_procedures[stmt.name] = stmt

        if stmt.security:
            self._validate_security(stmt.security, result)

        scope = set()
        for param in stmt.parameters:
            scope.add(param.name)

        self._validate_body(stmt.body, scope, result)
        self._validate_exception_handlers(stmt.exception_handlers, result)

    def _validate_body(self, stmts: list, scope: set[str], result: AnalysisResult):
        """Validate statements inside a workflow/procedure body."""
        for stmt in stmts:
            if isinstance(stmt, AssignmentStatement):
                scope.add(stmt.variable)
            elif isinstance(stmt, GenerateIntoStatement):
                if stmt.target_variable:
                    scope.add(stmt.target_variable)
            elif isinstance(stmt, EvaluateStatement):
                for wc in stmt.when_clauses:
                    self._validate_body(wc.statements, scope.copy(), result)
                if stmt.otherwise_statements:
                    self._validate_body(stmt.otherwise_statements, scope.copy(), result)
            elif isinstance(stmt, WhileStatement):
                self._validate_body(stmt.body, scope.copy(), result)
            elif isinstance(stmt, DoBlock):
                self._validate_body(stmt.statements, scope.copy(), result)
                self._validate_exception_handlers(stmt.exception_handlers, result)

    def _validate_exception_handlers(self, handlers: list[ExceptionHandler], result: AnalysisResult):
        """Validate exception handler types."""
        for handler in handlers:
            if handler.exception_type not in VALID_EXCEPTION_TYPES:
                result.warnings.append(AnalysisWarning(
                    f"Unknown exception type '{handler.exception_type}'. "
                    f"Known types: {', '.join(sorted(VALID_EXCEPTION_TYPES))}"
                ))

    def _validate_security(self, security: dict, result: AnalysisResult):
        """Validate security metadata."""
        if 'classification' in security:
            if security['classification'] not in VALID_CLASSIFICATIONS:
                result.warnings.append(AnalysisWarning(
                    f"Unknown classification level '{security['classification']}'. "
                    f"Valid levels: {', '.join(sorted(VALID_CLASSIFICATIONS))}"
                ))

    def _validate_accounting(self, accounting: dict, result: AnalysisResult):
        """Validate accounting metadata."""
        pass  # Accounting validation is flexible


def infer_condition_type(condition) -> str:
    """Determine if a condition is deterministic or semantic.

    Returns:
        'deterministic' - Can be evaluated without LLM
        'semantic' - Requires LLM to evaluate
    """
    if isinstance(condition, SemanticCondition):
        return 'semantic'
    if isinstance(condition, ComparisonCondition):
        return 'deterministic'
    return 'deterministic'
