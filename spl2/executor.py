"""SPL 2.0 Executor: execute PROMPT and WORKFLOW statements against LLM backends.

Extends SPL 1.0 executor with workflow execution engine:
- Variable state management (@var := expr)
- GENERATE ... INTO @var execution
- EVALUATE with semantic (LLM-judged) and deterministic conditions
- WHILE loops with iteration tracking
- EXCEPTION handling for LLM-specific failures
- COMMIT output finalization
- RETRY with fallback options
"""

from __future__ import annotations
import asyncio
import hashlib
import logging
import time
from dataclasses import dataclass, field

_log = logging.getLogger("spl2.executor")

from spl2.ast_nodes import (
    PromptStatement, SelectItem, SystemRoleCall, ContextRef,
    RagQuery, MemoryGet, Identifier, Literal, ParamRef,
    BinaryOp, FunctionCall, DottedName, NamedArg,
    WorkflowStatement, ProcedureStatement,
    EvaluateStatement, WhileStatement, DoBlock,
    AssignmentStatement, GenerateIntoStatement, CommitStatement,
    RetryStatement, RaiseStatement, CallStatement, SelectIntoStatement,
    SemanticCondition, ComparisonCondition, Condition, ExceptionHandler,
)
from spl2.optimizer import ExecutionPlan, ExecutionStep, WorkflowPlan
from spl2.adapters.base import LLMAdapter, GenerationResult
from spl2.adapters import get_adapter
from spl2.storage.memory import MemoryStore
from spl2.storage import get_vector_store
from spl2.token_counter import TokenCounter
from spl2.functions import FunctionRegistry


# ================================================================
# Result Types
# ================================================================

@dataclass
class SPLResult:
    """Result of executing an SPL PROMPT query."""
    content: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    latency_ms: float
    cost_usd: float | None = None
    plan: ExecutionPlan | None = None
    context_used: dict[str, str] = field(default_factory=dict)


@dataclass
class WorkflowResult:
    """Result of executing an SPL 2.0 WORKFLOW."""
    output: dict[str, str]
    status: str = "complete"
    total_llm_calls: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_latency_ms: float = 0
    total_cost_usd: float = 0.0
    committed_value: str | None = None
    committed_options: dict[str, str] = field(default_factory=dict)


# ================================================================
# Workflow Exceptions
# ================================================================

class SPLWorkflowError(Exception):
    """Base class for SPL workflow runtime errors."""
    pass


class HallucinationDetected(SPLWorkflowError):
    pass

class RefusalToAnswer(SPLWorkflowError):
    pass

class ContextLengthExceeded(SPLWorkflowError):
    pass

class ModelOverloaded(SPLWorkflowError):
    pass

class QualityBelowThreshold(SPLWorkflowError):
    pass

class MaxIterationsReached(SPLWorkflowError):
    pass

class BudgetExceeded(SPLWorkflowError):
    pass

class NodeUnavailable(SPLWorkflowError):
    pass


# Map exception type names to classes
EXCEPTION_CLASSES: dict[str, type[SPLWorkflowError]] = {
    'HallucinationDetected': HallucinationDetected,
    'RefusalToAnswer': RefusalToAnswer,
    'ContextLengthExceeded': ContextLengthExceeded,
    'ModelOverloaded': ModelOverloaded,
    'QualityBelowThreshold': QualityBelowThreshold,
    'MaxIterationsReached': MaxIterationsReached,
    'BudgetExceeded': BudgetExceeded,
    'NodeUnavailable': NodeUnavailable,
}


# ================================================================
# Workflow Execution State
# ================================================================

class WorkflowState:
    """Mutable state for workflow execution."""

    def __init__(self, params: dict[str, str] | None = None):
        self.variables: dict[str, str] = {}
        self.committed: bool = False
        self.committed_value: str | None = None
        self.committed_options: dict[str, str] = {}
        self.total_llm_calls: int = 0
        self.total_input_tokens: int = 0
        self.total_output_tokens: int = 0
        self.total_latency_ms: float = 0
        self.total_cost_usd: float = 0.0
        # Initialize from params
        if params:
            for k, v in params.items():
                self.variables[k] = str(v)

    def set_var(self, name: str, value: str):
        self.variables[name] = value

    def get_var(self, name: str) -> str:
        return self.variables.get(name, "")

    def record_llm_call(self, result: GenerationResult):
        self.total_llm_calls += 1
        self.total_input_tokens += result.input_tokens
        self.total_output_tokens += result.output_tokens
        self.total_latency_ms += result.latency_ms
        self.total_cost_usd += result.cost_usd or 0.0


# ================================================================
# Executor
# ================================================================

class Executor:
    """Execute SPL 2.0 PROMPT and WORKFLOW statements."""

    DEFAULT_MAX_ITERATIONS = 100

    def __init__(
        self,
        adapter_name: str = "echo",
        adapter: LLMAdapter | None = None,
        adapter_kwargs: dict | None = None,
        storage_dir: str = ".spl",
        cache_enabled: bool = False,
        cache_ttl: int = 3600,
    ):
        self.adapter = adapter or get_adapter(adapter_name, **(adapter_kwargs or {}))
        self._storage_dir_base = storage_dir
        self.memory = MemoryStore(f"{storage_dir}/memory.db")
        self.functions = FunctionRegistry()
        self.cache_enabled = cache_enabled
        self.cache_ttl = cache_ttl
        self._vector_store = None

    def register_tool(self, name: str, fn) -> "Executor":
        """Register a Python callable as a CALL-able tool. Returns self for chaining."""
        self.functions.register_tool(name, fn)
        return self

    @property
    def vector_store(self):
        """Lazily initialise the FAISS vector store on first access."""
        if self._vector_store is None:
            self._vector_store = get_vector_store("faiss", self._storage_dir_base)
        return self._vector_store

    # ================================================================
    # Top-Level Dispatch
    # ================================================================

    async def execute_program(
        self,
        analysis,
        params: dict[str, str] | None = None,
    ) -> list[SPLResult | WorkflowResult]:
        """Execute all statements in an analyzed program."""
        from spl2.optimizer import Optimizer
        optimizer = Optimizer()
        results = []

        # Register functions and procedures first
        for stmt in analysis.ast.statements:
            from spl2.ast_nodes import CreateFunctionStatement
            if isinstance(stmt, CreateFunctionStatement):
                self.functions.register(stmt)
            elif isinstance(stmt, ProcedureStatement):
                self.functions.register_procedure(stmt)

        for stmt in analysis.ast.statements:
            if isinstance(stmt, PromptStatement):
                plan = optimizer.optimize_single(stmt)
                result = await self.execute_prompt(plan, params=params, stmt=stmt)
                results.append(result)
            elif isinstance(stmt, WorkflowStatement):
                result = await self.execute_workflow(stmt, params=params)
                results.append(result)

        return results

    # ================================================================
    # PROMPT Execution (SPL 1.0 — simplified)
    # ================================================================

    async def execute_prompt(
        self,
        plan: ExecutionPlan,
        params: dict[str, str] | None = None,
        stmt: PromptStatement | None = None,
    ) -> SPLResult:
        """Execute an optimized PROMPT plan."""
        start = time.perf_counter()
        params = params or {}
        context_parts: dict[str, str] = {}
        system_prompt = None

        # Step 1a: Execute CTE sub-prompts in parallel
        cte_steps = [s for s in plan.steps if s.operation == "cte" and s.cte_stmt is not None]
        if cte_steps:
            _log.info("[%s] dispatching %d CTE(s) in parallel", plan.prompt_name, len(cte_steps))
            cte_tasks = [self._execute_cte_step(s, params) for s in cte_steps]
            cte_results = await asyncio.gather(*cte_tasks)
            for step, result_text in zip(cte_steps, cte_results):
                context_parts[step.alias] = result_text

        # Step 1b: Gather context for each non-CTE step
        for step in plan.steps:
            if step.operation == "system_role":
                system_prompt = self._resolve_system_role(step, stmt)
            elif step.operation == "load_context":
                context_parts[step.alias] = self._resolve_context(step, params)
            elif step.operation == "memory_get":
                context_parts[step.alias] = self._resolve_memory(step)
            elif step.operation == "rag_query":
                context_parts[step.alias] = self._resolve_rag(step, stmt, params)
            elif step.operation == "cte" and step.alias not in context_parts:
                context_parts[step.alias] = f"[CTE '{step.alias}' not resolved]"

        # Step 2: Apply token limits
        counter = TokenCounter(plan.model)
        for step in plan.steps:
            if step.alias in context_parts and step.allocated_tokens > 0:
                text = context_parts[step.alias]
                if counter.count(text) > step.allocated_tokens:
                    context_parts[step.alias] = counter.truncate_to_tokens(
                        text, step.allocated_tokens
                    )

        # Step 3: Assemble prompt
        prompt = self._assemble_prompt(context_parts, plan, stmt)

        # Step 4: Check prompt cache
        prompt_hash = hashlib.sha256(
            f"{plan.model}:{prompt}".encode()
        ).hexdigest()

        if self.cache_enabled:
            cached = self.memory.cache_get(prompt_hash)
            if cached is not None:
                _log.info("[%s] cache HIT", plan.prompt_name)
                latency = (time.perf_counter() - start) * 1000
                return SPLResult(
                    content=cached,
                    model=plan.model or "cached",
                    input_tokens=0,
                    output_tokens=0,
                    total_tokens=0,
                    latency_ms=latency,
                    cost_usd=0.0,
                    plan=plan,
                    context_used=context_parts,
                )

        # Step 5: Call LLM
        gen_result = await self.adapter.generate(
            prompt=prompt,
            model=plan.model or "",
            max_tokens=plan.output_budget,
            temperature=self._get_temperature(stmt),
            system=system_prompt,
        )

        latency = (time.perf_counter() - start) * 1000

        # Step 6: Store result if STORE clause exists
        if stmt and stmt.store_clause:
            self.memory.set(stmt.store_clause.key, gen_result.content)

        # Step 7: Cache result
        if self.cache_enabled:
            from datetime import datetime, timedelta
            expires = (datetime.utcnow() + timedelta(seconds=self.cache_ttl)).strftime("%Y-%m-%d %H:%M:%S")
            self.memory.cache_set(
                prompt_hash, gen_result.content,
                model=gen_result.model,
                tokens_used=gen_result.total_tokens,
                expires_at=expires,
            )
            _log.info("[%s] cache STORE (ttl=%ds)", plan.prompt_name, self.cache_ttl)

        return SPLResult(
            content=gen_result.content,
            model=gen_result.model,
            input_tokens=gen_result.input_tokens,
            output_tokens=gen_result.output_tokens,
            total_tokens=gen_result.total_tokens,
            latency_ms=latency,
            cost_usd=gen_result.cost_usd,
            plan=plan,
            context_used=context_parts,
        )

    def _resolve_system_role(self, step: ExecutionStep, stmt: PromptStatement | None) -> str:
        if stmt:
            for item in stmt.select_items:
                if isinstance(item.expression, SystemRoleCall):
                    return item.expression.description
        return "You are a helpful assistant."

    def _resolve_context(self, step: ExecutionStep, params: dict[str, str]) -> str:
        source = step.source
        if source.startswith("context."):
            field_name = source.split(".", 1)[1]
            for key in [source, field_name, f"context.{field_name}"]:
                if key in params:
                    return str(params[key])
        return f"[Context: {step.alias} - not provided]"

    async def _execute_cte_step(self, step: ExecutionStep, params: dict[str, str]) -> str:
        """Execute a CTE's nested PROMPT as a sub-query and return the result text."""
        from spl2.optimizer import Optimizer
        cte_stmt = step.cte_stmt
        if cte_stmt is None:
            return f"[CTE '{step.alias}' has no nested PROMPT]"
        _log.info("[CTE:%s] starting", step.alias)
        sub_plan = Optimizer().optimize_single(cte_stmt)
        result = await self.execute_prompt(sub_plan, params=params, stmt=cte_stmt)
        _log.info("[CTE:%s] done  tokens=%d  latency=%.0fms",
                  step.alias, result.total_tokens, result.latency_ms)
        return result.content

    def _resolve_memory(self, step: ExecutionStep) -> str:
        key = step.alias
        value = self.memory.get(key)
        return value or f"[Memory key '{key}' not found]"

    def _resolve_rag(self, step: ExecutionStep, stmt: PromptStatement | None,
                     params: dict[str, str] | None = None) -> str:
        """Resolve a rag_query step by searching the vector store."""
        try:
            query_text = ""
            top_k = 5
            if stmt:
                for item in stmt.select_items:
                    if isinstance(item.expression, RagQuery):
                        rq = item.expression
                        if isinstance(rq.query_text, Literal):
                            query_text = str(rq.query_text.value)
                        elif isinstance(rq.query_text, (DottedName, Identifier, ParamRef)):
                            # Resolve variable/param reference to its runtime value
                            ref_name = (
                                rq.query_text.full_name
                                if isinstance(rq.query_text, DottedName)
                                else rq.query_text.name
                            )
                            # DottedName like context.question → look up "question"
                            lookup = ref_name.split(".")[-1]
                            query_text = (params or {}).get(lookup, "")
                        else:
                            query_text = str(rq.query_text)
                        if rq.top_k is not None:
                            top_k = rq.top_k
                        break
            if not query_text:
                query_text = step.alias

            results = self.vector_store.query(query_text, top_k=top_k)
            if not results:
                return "[No RAG results found]"
            return "\n\n---\n\n".join(
                f"Document {i+1}:\n{r['text']}" for i, r in enumerate(results)
            )
        except Exception:
            _log.exception("RAG query failed")
            return "[RAG not initialized]"

    def _assemble_prompt(self, context: dict, plan: ExecutionPlan,
                         stmt: PromptStatement | None) -> str:
        parts = []
        for alias, text in context.items():
            if text and not text.startswith("["):
                parts.append(f"## {alias}\n{text}")

        if stmt and stmt.generate_clause:
            gen = stmt.generate_clause
            func_def = self.functions.get(gen.function_name)
            if func_def:
                arg_values: dict[str, str] = {}
                for param, arg in zip(func_def.parameters, gen.arguments):
                    if isinstance(arg, Identifier):
                        arg_values[param.name] = context.get(arg.name, "")
                    elif isinstance(arg, Literal):
                        arg_values[param.name] = str(arg.value)
                    else:
                        arg_values[param.name] = str(arg)
                task_text = func_def.body
                for key, val in arg_values.items():
                    task_text = task_text.replace("{" + key + "}", val)
                parts.append(f"\n## Task\n{task_text}")
            else:
                args_str = ", ".join(
                    a.name if isinstance(a, Identifier) else str(a)
                    for a in gen.arguments
                )
                parts.append(
                    f"\n## Task\n"
                    f"Based on the above context, generate: {gen.function_name}({args_str})"
                )

        return "\n\n".join(parts)

    def _get_temperature(self, stmt: PromptStatement | None) -> float:
        if stmt and stmt.generate_clause and stmt.generate_clause.temperature is not None:
            return stmt.generate_clause.temperature
        return 0.7

    # ================================================================
    # WORKFLOW Execution (SPL 2.0 — new)
    # ================================================================

    async def execute_workflow(
        self,
        stmt: WorkflowStatement,
        params: dict[str, str] | None = None,
    ) -> WorkflowResult:
        """Execute a WORKFLOW statement."""
        state = WorkflowState(params)
        start = time.perf_counter()

        # Initialize input variables: explicit params override defaults
        for inp in stmt.inputs:
            if params and inp.name in params:
                state.set_var(inp.name, str(params[inp.name]))
            elif inp.default_value is not None:
                state.set_var(inp.name, self._eval_expression(inp.default_value, state))

        try:
            await self._execute_body(stmt.body, state)
        except SPLWorkflowError as e:
            # Try to match exception handler
            handled = await self._handle_exception(e, stmt.exception_handlers, state)
            if not handled:
                raise

        total_latency = (time.perf_counter() - start) * 1000

        return WorkflowResult(
            output=dict(state.variables),
            status="complete" if state.committed else "no_commit",
            total_llm_calls=state.total_llm_calls,
            total_input_tokens=state.total_input_tokens,
            total_output_tokens=state.total_output_tokens,
            total_latency_ms=total_latency,
            total_cost_usd=state.total_cost_usd,
            committed_value=state.committed_value,
            committed_options=state.committed_options,
        )

    async def _execute_body(self, stmts: list, state: WorkflowState):
        """Execute a list of body statements."""
        for stmt in stmts:
            if state.committed:
                return  # Stop after COMMIT
            await self._execute_statement(stmt, state)

    async def _execute_statement(self, stmt, state: WorkflowState):
        """Execute a single statement inside a workflow."""
        if isinstance(stmt, AssignmentStatement):
            await self._exec_assignment(stmt, state)
        elif isinstance(stmt, GenerateIntoStatement):
            await self._exec_generate_into(stmt, state)
        elif isinstance(stmt, EvaluateStatement):
            await self._exec_evaluate(stmt, state)
        elif isinstance(stmt, WhileStatement):
            await self._exec_while(stmt, state)
        elif isinstance(stmt, CommitStatement):
            await self._exec_commit(stmt, state)
        elif isinstance(stmt, RetryStatement):
            pass  # Retry is handled at the exception level
        elif isinstance(stmt, RaiseStatement):
            await self._exec_raise(stmt, state)
        elif isinstance(stmt, CallStatement):
            await self._exec_call(stmt, state)
        elif isinstance(stmt, DoBlock):
            await self._exec_do_block(stmt, state)
        elif isinstance(stmt, SelectIntoStatement):
            await self._exec_select_into(stmt, state)
        else:
            _log.warning("Unknown statement type in workflow body: %s", type(stmt).__name__)

    # ================================================================
    # Statement Executors
    # ================================================================

    async def _exec_select_into(self, stmt: SelectIntoStatement, state: WorkflowState):
        """Execute WITH CTEs ... SELECT ... INTO @v1, @v2, ... (workflow fan-out)."""
        # Run each CTE and collect its generated content keyed by cte_name.field
        cte_results: dict[str, str] = {}
        for cte in stmt.ctes:
            if cte.nested_prompt:
                result = await self._exec_generate_into_prompt(cte.nested_prompt, state)
                # Key by cte_name.function_name (e.g. variant_a.response)
                gen = cte.nested_prompt.generate_clause
                field = gen.function_name if gen else "result"
                cte_results[f"{cte.name}.{field}"] = result
                cte_results[cte.name] = result  # also accessible by bare name

        # Evaluate SELECT items against cte_results.
        # DottedName expressions (e.g. response_1.answer) must be resolved
        # against cte_results, not state.variables — _eval_expression would
        # look in the wrong place and always return "".
        selected: list[str] = []
        for item in stmt.select_items:
            alias = getattr(item, 'alias', None)
            expr = item.expression if hasattr(item, 'expression') else None
            val = ""
            if expr is not None:
                if isinstance(expr, DottedName):
                    # e.g. response_1.answer -> cte_results["response_1.answer"]
                    # fall back to bare cte name if field-qualified key not found
                    val = cte_results.get(
                        expr.full_name,
                        cte_results.get(expr.full_name.split(".")[0], ""),
                    )
                else:
                    expr_str = self._eval_expression(expr, state)
                    val = cte_results.get(expr_str, "")
            # Direct lookup by alias as last resort
            if not val and alias:
                val = cte_results.get(str(alias), "")
            selected.append(val)

        # Assign to target variables (multi-var INTO)
        targets = stmt.target_variables or ([stmt.target_variable] if stmt.target_variable else [])
        for var, val in zip(targets, selected):
            state.set_var(var, val)
            _log.info("SELECT INTO: @%s (%d chars)", var, len(val) if val else 0)

    async def _exec_generate_into_prompt(self, prompt_stmt, state: WorkflowState) -> str:
        """Execute an inner PROMPT+GENERATE (from a CTE) and return the generated text."""
        gen = prompt_stmt.generate_clause
        if not gen:
            return ""

        args_text = [self._eval_expression(a, state) for a in gen.arguments]
        func_def = self.functions.get(gen.function_name)
        if func_def:
            prompt_text = func_def.body
            for param, arg_val in zip(func_def.parameters, args_text):
                prompt_text = prompt_text.replace("{" + param.name + "}", arg_val)
        else:
            prompt_text = f"Task: {gen.function_name}\n\n"
            for i, arg_text in enumerate(args_text):
                prompt_text += f"Input {i+1}:\n{arg_text}\n\n"

        model = gen.model or ""
        if model.startswith('@'):
            model = state.get_var(model[1:])

        _log.info("CTE GENERATE %s (model=%s)", gen.function_name, model or "default")
        gen_result = await self.adapter.generate(
            prompt=prompt_text,
            model=model,
            max_tokens=gen.output_budget or 1000,
            temperature=gen.temperature or 0.7,
        )
        state.record_llm_call(gen_result)
        _log.info("CTE GENERATE %s done (%d tokens, %.0fms)",
                  gen.function_name, gen_result.output_tokens, gen_result.latency_ms)
        return gen_result.content

    async def _exec_assignment(self, stmt: AssignmentStatement, state: WorkflowState):
        """Execute @var := expr"""
        value = self._eval_expression(stmt.expression, state)
        state.set_var(stmt.variable, value)
        _log.debug("Assignment: @%s = %s", stmt.variable, value[:100] if len(value) > 100 else value)

    async def _exec_generate_into(self, stmt: GenerateIntoStatement, state: WorkflowState):
        """Execute GENERATE func(args) INTO @var"""
        gen = stmt.generate_clause

        # Build the prompt from function name and arguments
        args_text = []
        for arg in gen.arguments:
            args_text.append(self._eval_expression(arg, state))

        prompt = f"Task: {gen.function_name}\n\n"
        for i, arg_text in enumerate(args_text):
            prompt += f"Input {i+1}:\n{arg_text}\n\n"

        # Check for user-defined function template
        func_def = self.functions.get(gen.function_name)
        if func_def:
            prompt = func_def.body
            for param, arg_val in zip(func_def.parameters, args_text):
                prompt = prompt.replace("{" + param.name + "}", arg_val)

        model = gen.model or ""
        if model.startswith('@'):
            model = state.get_var(model[1:])

        gen_result = await self.adapter.generate(
            prompt=prompt,
            model=model,
            max_tokens=gen.output_budget or 1000,
            temperature=gen.temperature or 0.7,
        )
        state.record_llm_call(gen_result)

        if stmt.target_variable:
            state.set_var(stmt.target_variable, gen_result.content)
            _log.info("GENERATE %s -> @%s (%d tokens, %.0fms)",
                      gen.function_name, stmt.target_variable,
                      gen_result.output_tokens, gen_result.latency_ms)

    async def _exec_evaluate(self, stmt: EvaluateStatement, state: WorkflowState):
        """Execute EVALUATE expr WHEN ... END"""
        eval_value = self._eval_expression(stmt.expression, state)

        for when_clause in stmt.when_clauses:
            cond = when_clause.condition
            matched = False

            if isinstance(cond, SemanticCondition):
                sv = cond.semantic_value
                if sv.startswith('contains:'):
                    # Deterministic substring check: contains:val1|val2|...
                    needles = sv[len('contains:'):].split('|')
                    lower_val = eval_value.lower()
                    matched = any(n.lower() in lower_val for n in needles)
                    _log.debug("EVALUATE contains %s -> %s", needles, matched)
                else:
                    # Use LLM to evaluate semantic condition
                    judge_prompt = (
                        f"Evaluate the following text and determine if it matches "
                        f"the condition '{sv}'.\n\n"
                        f"Text: {eval_value}\n\n"
                        f"Answer with only 'yes' or 'no'."
                    )
                    judge_result = await self.adapter.generate(
                        prompt=judge_prompt,
                        max_tokens=10,
                        temperature=0.0,
                    )
                    state.record_llm_call(judge_result)
                    matched = 'yes' in judge_result.content.lower()
                    _log.debug("EVALUATE semantic '%s' -> %s", sv, matched)

            elif isinstance(cond, ComparisonCondition):
                # Deterministic comparison
                try:
                    left_val = float(eval_value)
                    right_val = float(self._eval_expression(cond.right, state))
                    matched = self._compare(left_val, cond.operator, right_val)
                except (ValueError, TypeError):
                    matched = False
                _log.debug("EVALUATE %s %s %s -> %s",
                           eval_value[:20], cond.operator,
                           self._eval_expression(cond.right, state), matched)

            if matched:
                await self._execute_body(when_clause.statements, state)
                return

        # Otherwise clause
        if stmt.otherwise_statements:
            await self._execute_body(stmt.otherwise_statements, state)

    async def _exec_while(self, stmt: WhileStatement, state: WorkflowState):
        """Execute WHILE condition DO ... END"""
        iteration = 0
        max_iter = stmt.max_iterations or self.DEFAULT_MAX_ITERATIONS

        while iteration < max_iter:
            if state.committed:
                return

            # Evaluate condition
            cond = stmt.condition
            should_continue = False

            if isinstance(cond, Condition):
                try:
                    left_val = float(self._eval_expression(cond.left, state))
                    right_val = float(self._eval_expression(cond.right, state))
                    should_continue = self._compare(left_val, cond.operator, right_val)
                except (ValueError, TypeError):
                    should_continue = False
            elif isinstance(cond, SemanticCondition):
                # Semantic while condition — provide variable context for informed judgment
                context_lines = []
                for var_name, var_val in state.variables.items():
                    preview = var_val[:500] if len(var_val) > 500 else var_val
                    context_lines.append(f"  @{var_name} = {preview}")
                context_str = "\n".join(context_lines) if context_lines else "(no variables)"
                judge_prompt = (
                    f"Given the current state:\n{context_str}\n\n"
                    f"Is the condition '{cond.semantic_value}' still true?\n"
                    f"Answer with only 'yes' or 'no'."
                )
                judge_result = await self.adapter.generate(
                    prompt=judge_prompt,
                    max_tokens=10, temperature=0.0,
                )
                state.record_llm_call(judge_result)
                should_continue = 'yes' in judge_result.content.lower()
            else:
                # Expression-based condition (truthy check)
                val = self._eval_expression(cond, state)
                should_continue = bool(val and val != '0' and val.lower() != 'false')

            if not should_continue:
                break

            await self._execute_body(stmt.body, state)
            iteration += 1

        if iteration >= max_iter:
            raise MaxIterationsReached(f"WHILE loop exceeded {max_iter} iterations")

    async def _exec_commit(self, stmt: CommitStatement, state: WorkflowState):
        """Execute COMMIT expr WITH options"""
        value = self._eval_expression(stmt.expression, state)
        options = {}
        for k, v in stmt.options.items():
            options[k] = self._eval_expression(v, state)

        state.committed = True
        state.committed_value = value
        state.committed_options = options
        opts_str = ", ".join(f"{k}={v}" for k, v in options.items()) if options else "none"
        _log.info("COMMIT: %d chars | %s", len(value), opts_str)

    async def _exec_raise(self, stmt: RaiseStatement, state: WorkflowState):  # noqa: ARG002
        """Execute RAISE exception_type"""
        exc_cls = EXCEPTION_CLASSES.get(stmt.exception_type, SPLWorkflowError)
        raise exc_cls(stmt.message or stmt.exception_type)

    async def _exec_call(self, stmt: CallStatement, state: WorkflowState):
        """Execute CALL procedure(args) INTO @var"""
        import inspect

        # 1. Python tool takes priority — deterministic, no LLM cost
        tool = self.functions.get_tool(stmt.procedure_name)
        if tool is not None:
            args_text = [self._eval_expression(a, state) for a in stmt.arguments]
            if inspect.iscoroutinefunction(tool):
                result_str = await tool(*args_text)
            else:
                result_str = tool(*args_text)
            if stmt.target_variable:
                state.set_var(stmt.target_variable, str(result_str))
            _log.debug("Tool '%s' -> @%s", stmt.procedure_name, stmt.target_variable)
            return

        # 2. SPL PROCEDURE
        proc = self.functions.get_procedure(stmt.procedure_name)
        if proc is None:
            _log.warning("Procedure '%s' not found, using LLM fallback", stmt.procedure_name)
            # Fallback: use LLM to simulate the procedure
            args_text = [self._eval_expression(a, state) for a in stmt.arguments]
            prompt = f"Execute procedure: {stmt.procedure_name}({', '.join(args_text)})"
            result = await self.adapter.generate(prompt=prompt, max_tokens=1000)
            state.record_llm_call(result)
            if stmt.target_variable:
                state.set_var(stmt.target_variable, result.content)
            return

        # Execute the procedure body with its own state
        proc_state = WorkflowState()
        # Bind arguments: named args by name, positional args by position
        named_args = {a.name: a.value for a in stmt.arguments if isinstance(a, NamedArg)}
        positional_args = [a for a in stmt.arguments if not isinstance(a, NamedArg)]
        pos_idx = 0
        for param in proc.parameters:
            if param.name in named_args:
                proc_state.set_var(param.name, self._eval_expression(named_args[param.name], state))
            elif pos_idx < len(positional_args):
                proc_state.set_var(param.name, self._eval_expression(positional_args[pos_idx], state))
                pos_idx += 1
            elif param.default_value is not None:
                proc_state.set_var(param.name, self._eval_expression(param.default_value, state))

        try:
            await self._execute_body(proc.body, proc_state)
        except SPLWorkflowError as e:
            handled = await self._handle_exception(e, proc.exception_handlers, proc_state)
            if not handled:
                raise

        # Copy metrics back
        state.total_llm_calls += proc_state.total_llm_calls
        state.total_input_tokens += proc_state.total_input_tokens
        state.total_output_tokens += proc_state.total_output_tokens
        state.total_latency_ms += proc_state.total_latency_ms
        state.total_cost_usd += proc_state.total_cost_usd

        if stmt.target_variable and proc_state.committed_value:
            state.set_var(stmt.target_variable, proc_state.committed_value)

    async def _exec_do_block(self, stmt: DoBlock, state: WorkflowState):
        """Execute DO ... EXCEPTION ... END"""
        try:
            await self._execute_body(stmt.statements, state)
        except SPLWorkflowError as e:
            handled = await self._handle_exception(e, stmt.exception_handlers, state)
            if not handled:
                raise

    # ================================================================
    # Exception Handling
    # ================================================================

    async def _handle_exception(
        self, error: SPLWorkflowError,
        handlers: list[ExceptionHandler],
        state: WorkflowState,
    ) -> bool:
        """Try to handle an exception with the given handlers. Returns True if handled."""
        error_type = type(error).__name__

        for handler in handlers:
            if handler.exception_type == error_type or handler.exception_type in ('OTHERS', 'Others'):
                _log.info("Exception %s caught by handler '%s'", error_type, handler.exception_type)
                await self._execute_body(handler.statements, state)
                return True

        return False

    # ================================================================
    # Expression Evaluation
    # ================================================================

    def _eval_expression(self, expr, state: WorkflowState) -> str:
        """Evaluate an expression to a string value."""
        if isinstance(expr, Literal):
            return str(expr.value)
        elif isinstance(expr, ParamRef):
            return state.get_var(expr.name)
        elif isinstance(expr, Identifier):
            return state.get_var(expr.name)
        elif isinstance(expr, BinaryOp):
            left = self._eval_expression(expr.left, state)
            right = self._eval_expression(expr.right, state)
            if expr.op == '+':
                # Try numeric addition, fall back to string concatenation
                try:
                    result = float(left) + float(right)
                    return str(int(result)) if result == int(result) else str(result)
                except (ValueError, TypeError):
                    return left + right
            elif expr.op == '-':
                try:
                    result = float(left) - float(right)
                    return str(int(result)) if result == int(result) else str(result)
                except (ValueError, TypeError):
                    return left
        elif isinstance(expr, FunctionCall):
            if self.functions.is_builtin(expr.name):
                args = [self._eval_expression(a, state) for a in expr.arguments]
                return self.functions.call_builtin(expr.name, *args)
            return f"[{expr.name}(...)]"
        elif isinstance(expr, DottedName):
            return state.get_var(expr.full_name)
        elif isinstance(expr, NamedArg):
            return self._eval_expression(expr.value, state)
        return str(expr)

    def _compare(self, left: float, op: str, right: float) -> bool:
        """Evaluate a numeric comparison."""
        if op == '>':
            return left > right
        elif op == '<':
            return left < right
        elif op == '>=':
            return left >= right
        elif op == '<=':
            return left <= right
        elif op == '=':
            return left == right
        elif op == '!=':
            return left != right
        return False

    def close(self):
        """Clean up resources."""
        self.memory.close()
        if self._vector_store is not None:
            self._vector_store.close()
            self._vector_store = None
