"""SPL 2.0 Parser: hand-written recursive descent parser producing AST from tokens.

Extends SPL 1.0 parser with WORKFLOW, PROCEDURE, EVALUATE, WHILE, DO,
COMMIT, RETRY, RAISE, assignment, GENERATE...INTO, CALL, and SELECT...INTO.
"""

from spl.tokens import Token, TokenType
from spl.ast_nodes import (
    Program, PromptStatement, CreateFunctionStatement, ExplainStatement,
    ExecuteStatement, SelectItem, CTEClause, WhereClause, Condition,
    OrderByItem, GenerateClause, StoreClause, FromClause, Parameter,
    Expression, Literal, Identifier, DottedName, ParamRef, FunctionCall,
    BinaryOp, NamedArg, SystemRoleCall, ContextRef, RagQuery, MemoryGet,
    # SPL 2.0 new nodes
    WorkflowStatement, ProcedureStatement, DoBlock, ExceptionHandler,
    EvaluateStatement, WhenClause, SemanticCondition, ComparisonCondition,
    WhileStatement, CommitStatement, RetryStatement, RaiseStatement,
    AssignmentStatement, GenerateIntoStatement, CallStatement, SelectIntoStatement,
)


class ParseError(Exception):
    """Raised when the parser encounters unexpected tokens."""

    def __init__(self, message: str, token: Token):
        self.token = token
        super().__init__(f"Parse error at {token.line}:{token.column}: {message}")


class Parser:
    """Recursive descent parser for SPL 2.0."""

    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    def parse(self) -> Program:
        """Parse the full program."""
        statements = []
        while not self._check(TokenType.EOF):
            stmt = self._parse_statement()
            statements.append(stmt)
            # Optional semicolons between statements
            while self._check(TokenType.SEMICOLON):
                self._advance()
        return Program(statements=statements)

    # ================================================================
    # Statement Dispatch
    # ================================================================

    def _parse_statement(self):
        """Dispatch to the appropriate statement parser."""
        # SPL 1.0 statements
        if self._check(TokenType.PROMPT):
            return self._parse_prompt_statement()
        if self._check(TokenType.WITH):
            # Could be CTE block leading to PROMPT, or WITH inside workflow
            return self._parse_prompt_statement()
        if self._check(TokenType.CREATE):
            return self._parse_create_function()
        if self._check(TokenType.EXPLAIN):
            return self._parse_explain()
        if self._check(TokenType.EXECUTE):
            return self._parse_execute()

        # SPL 2.0 new statements
        if self._check(TokenType.WORKFLOW):
            return self._parse_workflow_statement()
        if self._check(TokenType.PROCEDURE):
            return self._parse_procedure_statement()
        if self._check(TokenType.EVALUATE):
            return self._parse_evaluate_statement()
        if self._check(TokenType.WHILE):
            return self._parse_while_statement()
        if self._check(TokenType.DO):
            return self._parse_do_block()
        if self._check(TokenType.COMMIT):
            return self._parse_commit_statement()
        if self._check(TokenType.RETRY):
            return self._parse_retry_statement()
        if self._check(TokenType.RAISE):
            return self._parse_raise_statement()
        if self._check(TokenType.CALL):
            return self._parse_call_statement()

        # GENERATE ... INTO @var (inside workflows)
        if self._check(TokenType.GENERATE):
            return self._parse_generate_into_statement()

        # SELECT ... INTO @var (inside workflows)
        if self._check(TokenType.SELECT):
            return self._parse_select_into_statement()

        # Assignment: @var := expr
        if self._check(TokenType.AT):
            return self._parse_assignment_statement()

        # SET @var = expr  (alias for assignment)
        if self._check(TokenType.SET):
            return self._parse_set_statement()

        raise ParseError(
            f"Expected statement keyword, got {self._current().type.name} ({self._current().value!r})",
            self._current()
        )

    # ================================================================
    # Statement parsers used inside workflow/procedure/do bodies
    # ================================================================

    def _parse_body_statement(self):
        """Parse a statement that can appear inside a DO block, WORKFLOW body, etc."""
        return self._parse_statement()

    def _is_body_end(self) -> bool:
        """Check if we've reached the end of a body (END, EXCEPTION, or EOF)."""
        return self._check_any(TokenType.END, TokenType.EXCEPTION, TokenType.EOF)

    def _is_when_or_end(self) -> bool:
        """Check if we've reached WHEN, OTHERWISE, or END."""
        return self._check_any(TokenType.WHEN, TokenType.OTHERWISE, TokenType.END, TokenType.EOF)

    # ================================================================
    # SPL 1.0: PROMPT Statement (unchanged)
    # ================================================================

    def _parse_cte_select_into(self, ctes: list) -> SelectIntoStatement:
        """Parse SELECT ... INTO @v1, @v2, ... after a CTE block (workflow pattern)."""
        select_items = self._parse_select_clause()

        from_clause = None
        if self._check(TokenType.FROM):
            from_clause = self._parse_from_clause()

        where_clause = None
        if self._check(TokenType.WHERE):
            where_clause = self._parse_where_clause()

        target_variables: list[str] = []
        if self._check(TokenType.INTO):
            self._advance()
            self._expect(TokenType.AT)
            target_variables.append(self._expect_identifier_or_keyword().value)
            while self._check(TokenType.COMMA):
                self._advance()
                self._expect(TokenType.AT)
                target_variables.append(self._expect_identifier_or_keyword().value)

        return SelectIntoStatement(
            select_items=select_items,
            from_clause=from_clause,
            where_clause=where_clause,
            target_variables=target_variables,
            ctes=ctes,
        )

    def _parse_prompt_statement(self):
        # Optional CTEs at the start: WITH <name> AS (...)
        ctes = []
        if self._check(TokenType.WITH) and not self._peek_is(TokenType.BUDGET) and not self._peek_is(TokenType.VRAM):
            ctes = self._parse_cte_block()

        # SPL 2.0: CTEs followed by SELECT ... INTO (workflow fan-out pattern)
        if ctes and self._check(TokenType.SELECT):
            return self._parse_cte_select_into(ctes)

        self._expect(TokenType.PROMPT)
        name = self._expect(TokenType.IDENTIFIER).value

        # Parse optional header clauses
        budget = None
        model = None
        cache_duration = None
        version = None

        # WITH BUDGET <n> TOKENS
        if self._check(TokenType.WITH) and self._peek_is(TokenType.BUDGET):
            self._advance()  # WITH
            self._advance()  # BUDGET
            budget = int(self._expect(TokenType.INTEGER).value)
            self._expect(TokenType.TOKENS)

        # USING MODEL <name>
        if self._check(TokenType.USING):
            self._advance()
            self._expect(TokenType.MODEL)
            if self._check(TokenType.STRING):
                model = self._advance().value
            else:
                model = self._read_model_name()

        # CACHE FOR <duration>
        if self._check(TokenType.CACHE):
            self._advance()
            self._expect(TokenType.FOR)
            dur_val = self._expect(TokenType.INTEGER).value
            dur_unit = self._expect(TokenType.IDENTIFIER).value
            cache_duration = f"{dur_val} {dur_unit}"

        # VERSION <version>
        if self._check(TokenType.VERSION):
            self._advance()
            if self._check(TokenType.FLOAT):
                version = self._advance().value
            elif self._check(TokenType.INTEGER):
                version = self._advance().value
            else:
                version = self._expect(TokenType.STRING).value

        # ON GRID [<url>]
        on_grid = None
        if self._check(TokenType.ON) and self._peek_is(TokenType.GRID):
            self._advance()  # ON
            self._advance()  # GRID
            if self._check(TokenType.STRING):
                on_grid = self._advance().value
            else:
                on_grid = ""

        # WITH VRAM <n>
        min_vram_gb = None
        if self._check(TokenType.WITH) and self._peek_is(TokenType.VRAM):
            self._advance()  # WITH
            self._advance()  # VRAM
            if self._check(TokenType.FLOAT):
                min_vram_gb = float(self._advance().value)
            else:
                min_vram_gb = float(self._expect(TokenType.INTEGER).value)

        # Parse optional CTEs after header: WITH <name> AS (...)
        if not ctes and self._check(TokenType.WITH) and not self._peek_is(TokenType.BUDGET) and not self._peek_is(TokenType.VRAM):
            ctes = self._parse_cte_block()

        # Parse SELECT clause
        select_items = self._parse_select_clause()

        # Parse optional WHERE clause
        where_clause = None
        if self._check(TokenType.WHERE):
            where_clause = self._parse_where_clause()

        # Parse optional ORDER BY clause
        order_by = None
        if self._check(TokenType.ORDER):
            order_by = self._parse_order_by()

        # Parse GENERATE clause
        generate_clause = None
        if self._check(TokenType.GENERATE):
            generate_clause = self._parse_generate_clause()

        # Parse optional STORE clause
        store_clause = None
        if self._check(TokenType.STORE):
            store_clause = self._parse_store_clause()

        return PromptStatement(
            name=name,
            budget=budget,
            model=model,
            cache_duration=cache_duration,
            version=version,
            on_grid=on_grid,
            min_vram_gb=min_vram_gb,
            ctes=ctes,
            select_items=select_items,
            where_clause=where_clause,
            order_by=order_by,
            generate_clause=generate_clause,
            store_clause=store_clause,
        )

    # ================================================================
    # SPL 1.0: CTE Block (unchanged)
    # ================================================================

    def _parse_cte_block(self) -> list[CTEClause]:
        self._expect(TokenType.WITH)
        ctes = [self._parse_cte_def()]
        while self._check(TokenType.COMMA):
            self._advance()
            ctes.append(self._parse_cte_def())
        return ctes

    def _parse_cte_def(self) -> CTEClause:
        name = self._expect(TokenType.IDENTIFIER).value
        self._expect(TokenType.AS)
        self._expect(TokenType.LPAREN)

        if self._check(TokenType.PROMPT) or self._check(TokenType.WITH):
            nested_prompt = self._parse_inner_prompt()
            self._expect(TokenType.RPAREN)
            return CTEClause(name=name, nested_prompt=nested_prompt)

        select_items = self._parse_select_clause()

        from_clause = None
        if self._check(TokenType.FROM):
            from_clause = self._parse_from_clause()

        where_clause = None
        if self._check(TokenType.WHERE):
            where_clause = self._parse_where_clause()

        limit_tokens = None
        if self._check(TokenType.LIMIT):
            self._advance()
            limit_tokens = int(self._expect(TokenType.INTEGER).value)
            self._expect(TokenType.TOKENS)

        self._expect(TokenType.RPAREN)

        return CTEClause(
            name=name,
            select_items=select_items,
            from_clause=from_clause,
            where_clause=where_clause,
            limit_tokens=limit_tokens,
        )

    def _parse_inner_prompt(self) -> PromptStatement:
        """Parse a PROMPT statement nested inside a CTE definition."""
        self._expect(TokenType.PROMPT)
        name = self._expect(TokenType.IDENTIFIER).value

        budget = None
        model = None

        if self._check(TokenType.WITH) and self._peek_is(TokenType.BUDGET):
            self._advance()  # WITH
            self._advance()  # BUDGET
            budget = int(self._expect(TokenType.INTEGER).value)
            self._expect(TokenType.TOKENS)

        if self._check(TokenType.USING):
            self._advance()
            self._expect(TokenType.MODEL)
            if self._check(TokenType.STRING):
                model = self._advance().value
            else:
                model = self._read_model_name()

        on_grid = None
        if self._check(TokenType.ON) and self._peek_is(TokenType.GRID):
            self._advance()
            self._advance()
            on_grid = self._advance().value if self._check(TokenType.STRING) else ""

        min_vram_gb = None
        if self._check(TokenType.WITH) and self._peek_is(TokenType.VRAM):
            self._advance()
            self._advance()
            if self._check(TokenType.FLOAT):
                min_vram_gb = float(self._advance().value)
            else:
                min_vram_gb = float(self._expect(TokenType.INTEGER).value)

        select_items = self._parse_select_clause()

        generate_clause = None
        if self._check(TokenType.GENERATE):
            generate_clause = self._parse_generate_clause()

        return PromptStatement(
            name=name, budget=budget, model=model,
            on_grid=on_grid, min_vram_gb=min_vram_gb,
            select_items=select_items, generate_clause=generate_clause,
        )

    # ================================================================
    # SPL 1.0: SELECT, FROM, WHERE, ORDER BY, GENERATE, STORE (unchanged)
    # ================================================================

    def _parse_select_clause(self) -> list[SelectItem]:
        self._expect(TokenType.SELECT)
        items = [self._parse_select_item()]
        while self._check(TokenType.COMMA):
            self._advance()
            if self._check_any(TokenType.WHERE, TokenType.ORDER, TokenType.GENERATE,
                               TokenType.STORE, TokenType.LIMIT, TokenType.RPAREN,
                               TokenType.INTO):
                break
            items.append(self._parse_select_item())
        return items

    def _parse_select_item(self) -> SelectItem:
        expr = self._parse_source_expression()

        alias = None
        if self._check(TokenType.AS):
            self._advance()
            alias = self._expect_identifier_or_keyword().value

        limit_tokens = None
        if self._check(TokenType.LIMIT):
            self._advance()
            limit_tokens = int(self._expect(TokenType.INTEGER).value)
            self._expect(TokenType.TOKENS)

        return SelectItem(expression=expr, alias=alias, limit_tokens=limit_tokens)

    def _parse_source_expression(self) -> Expression:
        """Parse a source expression: system_role(), context.*, rag.query(), memory.get(), or identifier."""
        tok = self._current()

        if tok.type == TokenType.IDENTIFIER and tok.value.lower() == "system_role":
            self._advance()
            self._expect(TokenType.LPAREN)
            desc = self._expect(TokenType.STRING).value
            self._expect(TokenType.RPAREN)
            return SystemRoleCall(description=desc)

        if tok.type == TokenType.IDENTIFIER and tok.value.lower() == "context":
            self._advance()
            self._expect(TokenType.DOT)
            field_name = self._expect_identifier_or_keyword().value
            return ContextRef(field_name=field_name)

        if tok.type == TokenType.IDENTIFIER and tok.value.lower() == "rag":
            self._advance()
            self._expect(TokenType.DOT)
            method = self._expect(TokenType.IDENTIFIER)
            if method.value.lower() != "query":
                raise ParseError(f"Expected 'query' after 'rag.', got '{method.value}'", method)
            self._expect(TokenType.LPAREN)
            query_text = self._parse_expression()
            top_k = None
            if self._check(TokenType.COMMA):
                self._advance()
                arg_name = self._expect(TokenType.IDENTIFIER)
                if arg_name.value.lower() != "top_k":
                    raise ParseError(f"Expected 'top_k', got '{arg_name.value}'", arg_name)
                self._expect(TokenType.EQ)
                top_k = int(self._expect(TokenType.INTEGER).value)
            self._expect(TokenType.RPAREN)
            return RagQuery(query_text=query_text, top_k=top_k)

        if tok.type == TokenType.IDENTIFIER and tok.value.lower() == "memory":
            self._advance()
            self._expect(TokenType.DOT)
            method = self._expect(TokenType.IDENTIFIER)
            if method.value.lower() != "get":
                raise ParseError(f"Expected 'get' after 'memory.', got '{method.value}'", method)
            self._expect(TokenType.LPAREN)
            key = self._expect(TokenType.STRING).value
            self._expect(TokenType.RPAREN)
            return MemoryGet(key=key)

        return self._parse_expression()

    def _parse_from_clause(self) -> FromClause:
        self._expect(TokenType.FROM)
        source = self._parse_source_expression()
        alias = None
        if self._check(TokenType.AS):
            self._advance()
            alias = self._expect(TokenType.IDENTIFIER).value
        return FromClause(source=source, alias=alias)

    def _parse_where_clause(self) -> WhereClause:
        self._expect(TokenType.WHERE)
        conditions = [self._parse_comparison_condition()]
        conjunctions = []

        while self._check_any(TokenType.AND, TokenType.OR):
            conj = self._advance().type.name
            conjunctions.append(conj)
            conditions.append(self._parse_comparison_condition())

        return WhereClause(conditions=conditions, conjunctions=conjunctions)

    def _parse_comparison_condition(self) -> Condition:
        """Parse a deterministic comparison condition: expr op expr."""
        left = self._parse_expression()

        op_map = {
            TokenType.EQ: "=",
            TokenType.NEQ: "!=",
            TokenType.GT: ">",
            TokenType.LT: "<",
            TokenType.GTE: ">=",
            TokenType.LTE: "<=",
            TokenType.IN: "IN",
        }

        tok = self._current()
        if tok.type not in op_map:
            raise ParseError(
                f"Expected comparison operator, got {tok.type.name}", tok
            )
        op = op_map[tok.type]
        self._advance()

        if op == "IN":
            self._expect(TokenType.LPAREN)
            values = [self._parse_expression()]
            while self._check(TokenType.COMMA):
                self._advance()
                values.append(self._parse_expression())
            self._expect(TokenType.RPAREN)
            right = FunctionCall(name="__in_list__", arguments=values)
        else:
            right = self._parse_expression()

        return Condition(left=left, operator=op, right=right)

    def _parse_order_by(self) -> list[OrderByItem]:
        self._expect(TokenType.ORDER)
        self._expect(TokenType.BY)
        items = [self._parse_order_item()]
        while self._check(TokenType.COMMA):
            self._advance()
            items.append(self._parse_order_item())
        return items

    def _parse_order_item(self) -> OrderByItem:
        expr = self._parse_expression()
        direction = "ASC"
        if self._check(TokenType.ASC):
            self._advance()
        elif self._check(TokenType.DESC):
            self._advance()
            direction = "DESC"
        return OrderByItem(expression=expr, direction=direction)

    def _parse_generate_clause(self) -> GenerateClause:
        self._expect(TokenType.GENERATE)
        func_name = self._expect_identifier_or_keyword().value

        self._expect(TokenType.LPAREN)
        arguments: list[Expression] = []
        if not self._check(TokenType.RPAREN):
            arguments.append(self._parse_expression())
            while self._check(TokenType.COMMA):
                self._advance()
                arguments.append(self._parse_expression())
        self._expect(TokenType.RPAREN)

        output_budget = None
        temperature = None
        output_format = None
        schema = None

        # Only consume WITH if followed by GENERATE-specific options
        generate_with_tokens = {TokenType.OUTPUT, TokenType.TEMPERATURE, TokenType.FORMAT, TokenType.SCHEMA}
        if self._check(TokenType.WITH) and self.pos + 1 < len(self.tokens) and self.tokens[self.pos + 1].type in generate_with_tokens:
            self._advance()
            while True:
                if self._check(TokenType.OUTPUT):
                    self._advance()
                    self._expect(TokenType.BUDGET)
                    output_budget = int(self._expect(TokenType.INTEGER).value)
                    self._expect(TokenType.TOKENS)
                elif self._check(TokenType.TEMPERATURE):
                    self._advance()
                    if self._check(TokenType.FLOAT):
                        temperature = float(self._advance().value)
                    else:
                        temperature = float(self._expect(TokenType.INTEGER).value)
                elif self._check(TokenType.FORMAT):
                    self._advance()
                    output_format = self._expect(TokenType.IDENTIFIER).value
                elif self._check(TokenType.SCHEMA):
                    self._advance()
                    schema = self._expect(TokenType.IDENTIFIER).value
                else:
                    break
                if self._check(TokenType.COMMA):
                    self._advance()
                else:
                    break

        # Parse optional USING MODEL '<model>' or USING MODEL @var
        model = None
        if self._check(TokenType.USING):
            self._advance()
            self._expect(TokenType.MODEL)
            if self._check(TokenType.STRING):
                model = self._advance().value
            elif self._check(TokenType.AT):
                self._advance()
                model = '@' + self._expect_identifier_or_keyword().value
            else:
                model = self._expect(TokenType.IDENTIFIER).value

        return GenerateClause(
            function_name=func_name,
            arguments=arguments,
            output_budget=output_budget,
            temperature=temperature,
            output_format=output_format,
            schema=schema,
            model=model,
        )

    def _parse_store_clause(self) -> StoreClause:
        self._expect(TokenType.STORE)
        self._expect(TokenType.RESULT)
        self._expect(TokenType.IN)

        mem_tok = self._expect(TokenType.IDENTIFIER)
        if mem_tok.value.lower() != "memory":
            raise ParseError(f"Expected 'memory' after STORE RESULT IN, got '{mem_tok.value}'", mem_tok)
        self._expect(TokenType.DOT)
        key = self._expect_identifier_or_keyword().value

        return StoreClause(key=key)

    # ================================================================
    # SPL 1.0: CREATE FUNCTION, EXPLAIN, EXECUTE (unchanged)
    # ================================================================

    def _parse_create_function(self) -> CreateFunctionStatement:
        self._expect(TokenType.CREATE)
        self._expect(TokenType.FUNCTION)
        name = self._expect(TokenType.IDENTIFIER).value

        self._expect(TokenType.LPAREN)
        parameters: list[Parameter] = []
        if not self._check(TokenType.RPAREN):
            parameters.append(self._parse_parameter())
            while self._check(TokenType.COMMA):
                self._advance()
                parameters.append(self._parse_parameter())
        self._expect(TokenType.RPAREN)

        self._expect(TokenType.RETURNS)
        return_type = self._expect(TokenType.IDENTIFIER).value

        self._expect(TokenType.AS)
        self._expect(TokenType.DOLLAR_DOLLAR)
        body = self._expect(TokenType.STRING).value

        return CreateFunctionStatement(
            name=name, parameters=parameters,
            return_type=return_type, body=body,
        )

    def _parse_parameter(self) -> Parameter:
        name = self._expect_identifier_or_keyword().value
        param_type = None
        default_value = None
        if self._check(TokenType.IDENTIFIER) and not self._check_any(TokenType.COMMA, TokenType.RPAREN, TokenType.DEFAULT):
            param_type = self._advance().value
        if self._check(TokenType.DEFAULT):
            self._advance()
            default_value = self._parse_expression()
        return Parameter(name=name, param_type=param_type, default_value=default_value)

    def _parse_explain(self) -> ExplainStatement:
        self._expect(TokenType.EXPLAIN)
        self._expect(TokenType.PROMPT)
        name = self._expect(TokenType.IDENTIFIER).value
        return ExplainStatement(prompt_name=name)

    def _parse_execute(self) -> ExecuteStatement:
        self._expect(TokenType.EXECUTE)
        self._expect(TokenType.PROMPT)
        name = self._expect(TokenType.IDENTIFIER).value

        params: dict[str, Expression] = {}
        if self._check(TokenType.WITH):
            self._advance()
            self._expect(TokenType.PARAMS)
            self._expect(TokenType.LPAREN)

            if not self._check(TokenType.RPAREN):
                key, val = self._parse_param_assignment()
                params[key] = val
                while self._check(TokenType.COMMA):
                    self._advance()
                    key, val = self._parse_param_assignment()
                    params[key] = val

            self._expect(TokenType.RPAREN)

        return ExecuteStatement(prompt_name=name, params=params)

    def _parse_param_assignment(self) -> tuple[str, Expression]:
        parts = [self._expect(TokenType.IDENTIFIER).value]
        while self._check(TokenType.DOT):
            self._advance()
            parts.append(self._expect(TokenType.IDENTIFIER).value)
        key = '.'.join(parts)
        self._expect(TokenType.EQ)
        value = self._parse_expression()
        return key, value

    # ================================================================
    # SPL 2.0: WORKFLOW Statement
    # ================================================================

    def _parse_workflow_statement(self) -> WorkflowStatement:
        """Parse WORKFLOW name INPUT ... OUTPUT ... DO ... END"""
        self._expect(TokenType.WORKFLOW)
        name = self._expect(TokenType.IDENTIFIER).value

        # INPUT: @param type, ...
        inputs = []
        if self._check(TokenType.INPUT):
            self._advance()
            if self._check(TokenType.COLON):
                self._advance()
            inputs = self._parse_workflow_param_list()

        # OUTPUT: @param type, ...
        outputs = []
        if self._check(TokenType.OUTPUT):
            self._advance()
            if self._check(TokenType.COLON):
                self._advance()
            outputs = self._parse_workflow_param_list()

        # Optional metadata blocks
        security = None
        if self._check(TokenType.SECURITY):
            security = self._parse_security_block()

        accounting = None
        if self._check(TokenType.ACCOUNTING):
            accounting = self._parse_accounting_block()

        labels = None
        if self._check(TokenType.LABELS):
            labels = self._parse_labels_block()

        # DO ... [EXCEPTION ...] END
        do_block = self._parse_do_block()

        return WorkflowStatement(
            name=name,
            inputs=inputs,
            outputs=outputs,
            security=security,
            accounting=accounting,
            labels=labels,
            body=do_block.statements,
            exception_handlers=do_block.exception_handlers,
        )

    def _parse_workflow_param_list(self) -> list[Parameter]:
        """Parse @param type, @param type DEFAULT value, ..."""
        params = [self._parse_workflow_param()]
        while self._check(TokenType.COMMA):
            self._advance()
            # Stop if next is a section keyword
            if self._check_any(TokenType.OUTPUT, TokenType.INPUT, TokenType.DO,
                               TokenType.SECURITY, TokenType.ACCOUNTING, TokenType.LABELS):
                break
            params.append(self._parse_workflow_param())
        return params

    def _parse_workflow_param(self) -> Parameter:
        """Parse @name type [DEFAULT value]."""
        self._expect(TokenType.AT)
        name = self._expect_identifier_or_keyword().value
        param_type = None
        default_value = None

        # Optional type
        if self._check(TokenType.IDENTIFIER):
            param_type = self._advance().value

        # Optional DEFAULT
        if self._check(TokenType.DEFAULT):
            self._advance()
            default_value = self._parse_expression()

        return Parameter(name=name, param_type=param_type, default_value=default_value)

    # ================================================================
    # SPL 2.0: PROCEDURE Statement
    # ================================================================

    def _parse_procedure_statement(self) -> ProcedureStatement:
        """Parse PROCEDURE name(params) RETURNS type DO ... END"""
        self._expect(TokenType.PROCEDURE)
        name = self._expect(TokenType.IDENTIFIER).value

        # Parameters in parentheses
        self._expect(TokenType.LPAREN)
        parameters = []
        if not self._check(TokenType.RPAREN):
            parameters.append(self._parse_parameter())
            while self._check(TokenType.COMMA):
                self._advance()
                parameters.append(self._parse_parameter())
        self._expect(TokenType.RPAREN)

        # Optional RETURNS type
        return_type = None
        if self._check(TokenType.RETURNS):
            self._advance()
            return_type = self._expect(TokenType.IDENTIFIER).value

        # Optional metadata
        security = None
        if self._check(TokenType.SECURITY):
            security = self._parse_security_block()

        accounting = None
        if self._check(TokenType.ACCOUNTING):
            accounting = self._parse_accounting_block()

        # DO ... END
        do_block = self._parse_do_block()

        return ProcedureStatement(
            name=name,
            parameters=parameters,
            return_type=return_type,
            security=security,
            accounting=accounting,
            body=do_block.statements,
            exception_handlers=do_block.exception_handlers,
        )

    # ================================================================
    # SPL 2.0: DO Block
    # ================================================================

    def _parse_do_block(self) -> DoBlock:
        """Parse DO statements [EXCEPTION handlers] END"""
        self._expect(TokenType.DO)

        statements = []
        while not self._is_body_end():
            statements.append(self._parse_body_statement())
            while self._check(TokenType.SEMICOLON):
                self._advance()

        exception_handlers = []
        if self._check(TokenType.EXCEPTION):
            exception_handlers = self._parse_exception_block()

        self._expect(TokenType.END)

        return DoBlock(statements=statements, exception_handlers=exception_handlers)

    def _parse_exception_block(self) -> list[ExceptionHandler]:
        """Parse EXCEPTION WHEN type THEN statements ..."""
        self._expect(TokenType.EXCEPTION)

        handlers = []
        while self._check(TokenType.WHEN):
            self._advance()  # WHEN
            # Exception type can be an identifier or OTHERS keyword
            if self._check(TokenType.OTHERS):
                exception_type = self._advance().value
            else:
                exception_type = self._expect_identifier_or_keyword().value
            self._expect(TokenType.THEN)

            handler_stmts = []
            while not self._check_any(TokenType.WHEN, TokenType.END, TokenType.EOF):
                handler_stmts.append(self._parse_body_statement())
                while self._check(TokenType.SEMICOLON):
                    self._advance()

            handlers.append(ExceptionHandler(
                exception_type=exception_type,
                statements=handler_stmts,
            ))

        return handlers

    # ================================================================
    # SPL 2.0: EVALUATE Statement
    # ================================================================

    def _parse_evaluate_statement(self) -> EvaluateStatement:
        """Parse EVALUATE expr WHEN condition THEN statements ... END"""
        self._expect(TokenType.EVALUATE)
        expression = self._parse_expression()

        when_clauses = []
        while self._check(TokenType.WHEN):
            self._advance()  # WHEN
            condition = self._parse_evaluate_condition()
            self._expect(TokenType.THEN)

            then_stmts = []
            while not self._is_when_or_end():
                then_stmts.append(self._parse_body_statement())
                while self._check(TokenType.SEMICOLON):
                    self._advance()

            when_clauses.append(WhenClause(
                condition=condition,
                statements=then_stmts,
            ))

        otherwise_stmts = []
        if self._check(TokenType.OTHERWISE):
            self._advance()
            while not self._check_any(TokenType.END, TokenType.EOF):
                otherwise_stmts.append(self._parse_body_statement())
                while self._check(TokenType.SEMICOLON):
                    self._advance()

        self._expect(TokenType.END)

        return EvaluateStatement(
            expression=expression,
            when_clauses=when_clauses,
            otherwise_statements=otherwise_stmts,
        )

    def _parse_evaluate_condition(self):
        """Parse a condition in EVALUATE context.

        Can be:
        - Semantic: 'coherent', 'complete' (string literal)
        - Comparison: > 0.8, <= 0.5, = 'value'
        """
        # Semantic condition: string literal
        if self._check(TokenType.STRING):
            value = self._advance().value
            return SemanticCondition(semantic_value=value)

        # Comparison condition: operator + expression
        op_map = {
            TokenType.GT: ">",
            TokenType.LT: "<",
            TokenType.GTE: ">=",
            TokenType.LTE: "<=",
            TokenType.EQ: "=",
            TokenType.NEQ: "!=",
        }
        tok = self._current()
        if tok.type in op_map:
            op = op_map[tok.type]
            self._advance()
            right = self._parse_expression()
            return ComparisonCondition(operator=op, right=right)

        # contains('value') [OR contains('value')]* — semantic substring condition
        if tok.type == TokenType.IDENTIFIER and tok.value.lower() == 'contains':
            values: list[str] = []
            while self._check(TokenType.IDENTIFIER) and self._current().value.lower() == 'contains':
                self._advance()  # contains
                self._expect(TokenType.LPAREN)
                values.append(self._expect(TokenType.STRING).value)
                self._expect(TokenType.RPAREN)
                if not self._check(TokenType.OR):
                    break
                self._advance()  # OR
            # Encode as a semantic condition with all values joined
            return SemanticCondition(semantic_value='contains:' + '|'.join(values))

        # Fall through: could be an expression-based condition
        raise ParseError(
            f"Expected condition (string literal or comparison operator), got {tok.type.name}",
            tok
        )

    # ================================================================
    # SPL 2.0: WHILE Statement
    # ================================================================

    def _parse_while_statement(self) -> WhileStatement:
        """Parse WHILE condition DO statements END"""
        self._expect(TokenType.WHILE)

        condition = self._parse_while_condition()

        self._expect(TokenType.DO)

        body = []
        while not self._check_any(TokenType.END, TokenType.EOF):
            body.append(self._parse_body_statement())
            while self._check(TokenType.SEMICOLON):
                self._advance()

        self._expect(TokenType.END)

        return WhileStatement(condition=condition, body=body)

    def _parse_while_condition(self):
        """Parse a WHILE condition which can be a comparison or compound expression."""
        left = self._parse_expression()

        # Check for comparison operator
        op_map = {
            TokenType.GT: ">",
            TokenType.LT: "<",
            TokenType.GTE: ">=",
            TokenType.LTE: "<=",
            TokenType.EQ: "=",
            TokenType.NEQ: "!=",
        }

        tok = self._current()
        if tok.type in op_map:
            op = op_map[tok.type]
            self._advance()
            right = self._parse_expression()
            condition = Condition(left=left, operator=op, right=right)

            # Check for AND/OR compound conditions
            while self._check_any(TokenType.AND, TokenType.OR):
                self._advance()  # AND/OR
                if self._check(TokenType.NOT):
                    self._advance()
                    # AND NOT EVALUATE 'condition' FROM ...
                    if self._check(TokenType.EVALUATE):
                        self._advance()
                        self._expect(TokenType.STRING)  # semantic value
                        # Optional FROM clause
                        if self._check(TokenType.FROM):
                            self._advance()
                            # Skip the FROM args until DO
                            while not self._check(TokenType.DO):
                                self._advance()
                        return condition
                # Simple compound: AND expr op expr
                self._parse_expression()
                if self._current().type in op_map:
                    self._advance()
                    self._parse_expression()

            return condition

        # If no operator, it could be a semantic condition in string form
        return left

    # ================================================================
    # SPL 2.0: COMMIT Statement
    # ================================================================

    def _parse_commit_statement(self) -> CommitStatement:
        """Parse COMMIT expr [WITH key=value, ...]"""
        self._expect(TokenType.COMMIT)
        expression = self._parse_expression()

        options = {}
        if self._check(TokenType.WITH):
            self._advance()
            while True:
                key = self._expect_identifier_or_keyword().value
                self._expect(TokenType.EQ)
                value = self._parse_expression()
                options[key] = value

                if not self._check(TokenType.COMMA):
                    break
                self._advance()

        return CommitStatement(expression=expression, options=options)

    # ================================================================
    # SPL 2.0: RETRY Statement
    # ================================================================

    def _parse_retry_statement(self) -> RetryStatement:
        """Parse RETRY [WITH key=value, ...]"""
        self._expect(TokenType.RETRY)

        options = {}
        if self._check(TokenType.WITH):
            self._advance()
            while True:
                key = self._expect_identifier_or_keyword().value
                self._expect(TokenType.EQ)
                value = self._parse_expression()
                options[key] = value

                if not self._check(TokenType.COMMA):
                    break
                self._advance()

        return RetryStatement(options=options)

    # ================================================================
    # SPL 2.0: RAISE Statement
    # ================================================================

    def _parse_raise_statement(self) -> RaiseStatement:
        """Parse RAISE exception_type ['message']"""
        self._expect(TokenType.RAISE)
        exception_type = self._expect_identifier_or_keyword().value

        message = None
        if self._check(TokenType.STRING):
            message = self._advance().value

        return RaiseStatement(exception_type=exception_type, message=message)

    # ================================================================
    # SPL 2.0: Assignment Statement
    # ================================================================

    def _parse_set_statement(self) -> AssignmentStatement:
        """Parse SET @var = expr  (SQL-style assignment alias)."""
        self._expect(TokenType.SET)
        self._expect(TokenType.AT)
        var_name = self._expect_identifier_or_keyword().value
        self._expect(TokenType.EQ)
        value = self._parse_expression()
        return AssignmentStatement(variable=var_name, expression=value)

    def _parse_assignment_statement(self) -> AssignmentStatement:
        """Parse @var := expr"""
        self._expect(TokenType.AT)
        var_name = self._expect_identifier_or_keyword().value
        self._expect(TokenType.ASSIGN)
        expression = self._parse_expression()

        return AssignmentStatement(variable=var_name, expression=expression)

    # ================================================================
    # SPL 2.0: GENERATE ... INTO @var
    # ================================================================

    def _parse_generate_into_statement(self) -> GenerateIntoStatement:
        """Parse GENERATE func(args) [WITH options] INTO @var"""
        gen_clause = self._parse_generate_clause()

        target = None
        if self._check(TokenType.INTO):
            self._advance()
            self._expect(TokenType.AT)
            target = self._expect_identifier_or_keyword().value

        return GenerateIntoStatement(
            generate_clause=gen_clause,
            target_variable=target,
        )

    # ================================================================
    # SPL 2.0: CALL Statement
    # ================================================================

    def _parse_call_statement(self) -> CallStatement:
        """Parse CALL procedure(args) [INTO @var]"""
        self._expect(TokenType.CALL)
        proc_name = self._expect(TokenType.IDENTIFIER).value

        self._expect(TokenType.LPAREN)
        arguments: list[Expression] = []
        if not self._check(TokenType.RPAREN):
            arguments.append(self._parse_call_argument())
            while self._check(TokenType.COMMA):
                self._advance()
                arguments.append(self._parse_call_argument())
        self._expect(TokenType.RPAREN)

        target = None
        if self._check(TokenType.INTO):
            self._advance()
            self._expect(TokenType.AT)
            target = self._expect_identifier_or_keyword().value

        return CallStatement(
            procedure_name=proc_name,
            arguments=arguments,
            target_variable=target,
        )

    # ================================================================
    # SPL 2.0: SELECT ... INTO @var
    # ================================================================

    def _parse_select_into_statement(self) -> SelectIntoStatement:
        """Parse SELECT ... [FROM ...] [WHERE ...] INTO @var"""
        select_items = self._parse_select_clause()

        from_clause = None
        if self._check(TokenType.FROM):
            from_clause = self._parse_from_clause()

        where_clause = None
        if self._check(TokenType.WHERE):
            where_clause = self._parse_where_clause()

        target = None
        if self._check(TokenType.INTO):
            self._advance()
            self._expect(TokenType.AT)
            target = self._expect_identifier_or_keyword().value

        return SelectIntoStatement(
            select_items=select_items,
            from_clause=from_clause,
            where_clause=where_clause,
            target_variable=target,
        )

    # ================================================================
    # SPL 2.0: Metadata Blocks
    # ================================================================

    def _parse_security_block(self) -> dict:
        """Parse SECURITY: CLASSIFICATION: level, ..."""
        self._expect(TokenType.SECURITY)
        self._expect(TokenType.COLON)
        security = {}

        while self._check(TokenType.CLASSIFICATION):
            self._advance()
            self._expect(TokenType.COLON)
            security['classification'] = self._expect(TokenType.IDENTIFIER).value

        return security

    def _parse_accounting_block(self) -> dict:
        """Parse ACCOUNTING: BILLABLE_TO: '...', BUDGET_LIMIT: N moma_points, ..."""
        self._expect(TokenType.ACCOUNTING)
        self._expect(TokenType.COLON)
        accounting = {}

        while self._check(TokenType.IDENTIFIER) or self._check(TokenType.STRING):
            tok = self._current()
            if tok.type == TokenType.IDENTIFIER:
                key = self._advance().value.lower()
                self._expect(TokenType.COLON)
                if self._check(TokenType.STRING):
                    accounting[key] = self._advance().value
                elif self._check(TokenType.INTEGER):
                    accounting[key] = int(self._advance().value)
                elif self._check(TokenType.FLOAT):
                    accounting[key] = float(self._advance().value)
                else:
                    break
            else:
                break

        return accounting

    def _parse_labels_block(self) -> dict:
        """Parse LABELS: { 'key': 'value', ... }"""
        self._expect(TokenType.LABELS)
        self._expect(TokenType.COLON)
        self._expect(TokenType.LBRACE)

        labels = {}
        if not self._check(TokenType.RBRACE):
            key = self._expect(TokenType.STRING).value
            self._expect(TokenType.COLON)
            value = self._expect(TokenType.STRING).value
            labels[key] = value

            while self._check(TokenType.COMMA):
                self._advance()
                if self._check(TokenType.RBRACE):
                    break
                key = self._expect(TokenType.STRING).value
                self._expect(TokenType.COLON)
                value = self._expect(TokenType.STRING).value
                labels[key] = value

        self._expect(TokenType.RBRACE)
        return labels

    # ================================================================
    # Expression Parsing (extended for SPL 2.0)
    # ================================================================

    def _parse_expression(self) -> Expression:
        """Parse an expression with optional +/- operations."""
        left = self._parse_primary()

        while self._check_any(TokenType.PLUS, TokenType.MINUS):
            op = self._advance().value
            right = self._parse_primary()
            left = BinaryOp(left=left, op=op, right=right)

        return left

    def _parse_primary(self) -> Expression:
        """Parse a primary expression."""
        tok = self._current()

        # @param reference — allow keywords as variable names after @
        if tok.type == TokenType.AT:
            self._advance()
            name = self._expect_identifier_or_keyword().value
            return ParamRef(name=name)

        # String literal
        if tok.type == TokenType.STRING:
            self._advance()
            return Literal(value=tok.value, literal_type="string")

        # Integer literal
        if tok.type == TokenType.INTEGER:
            self._advance()
            return Literal(value=int(tok.value), literal_type="integer")

        # Float literal
        if tok.type == TokenType.FLOAT:
            self._advance()
            return Literal(value=float(tok.value), literal_type="float")

        # Identifier (possibly dotted, possibly function call)
        if tok.type == TokenType.IDENTIFIER:
            return self._parse_identifier_expression()

        # Keywords used as identifiers in expression context
        keyword_as_expr = {
            TokenType.FORMAT, TokenType.MODEL, TokenType.RESULT,
            TokenType.VERSION, TokenType.SCHEMA, TokenType.ERROR,
            TokenType.OUTPUT, TokenType.INPUT, TokenType.TEMPERATURE,
            TokenType.PROMPT, TokenType.BUDGET, TokenType.TOKENS,
            TokenType.ORDER, TokenType.FROM, TokenType.WHERE,
            TokenType.WORKFLOW, TokenType.PROCEDURE, TokenType.DEFAULT,
            TokenType.SECURITY, TokenType.ACCOUNTING, TokenType.CLASSIFICATION,
        }
        if tok.type in keyword_as_expr:
            self._advance()
            return Identifier(name=tok.value)

        # Parenthesized expression
        if tok.type == TokenType.LPAREN:
            self._advance()
            expr = self._parse_expression()
            self._expect(TokenType.RPAREN)
            return expr

        raise ParseError(f"Expected expression, got {tok.type.name} ({tok.value!r})", tok)

    def _parse_identifier_expression(self) -> Expression:
        """Parse an identifier that might be dotted or a function call."""
        name = self._advance().value  # consume identifier

        # Function call: name(...)
        if self._check(TokenType.LPAREN):
            self._advance()  # (
            args: list[Expression] = []
            if not self._check(TokenType.RPAREN):
                args.append(self._parse_call_argument())
                while self._check(TokenType.COMMA):
                    self._advance()
                    args.append(self._parse_call_argument())
            self._expect(TokenType.RPAREN)
            return FunctionCall(name=name, arguments=args)

        # Dotted name: name.field.subfield
        if self._check(TokenType.DOT):
            parts = [name]
            while self._check(TokenType.DOT):
                self._advance()
                parts.append(self._expect_identifier_or_keyword().value)
            return DottedName(parts=parts)

        return Identifier(name=name)

    def _parse_call_argument(self) -> Expression:
        """Parse a function argument, which might be a named arg (key=value)."""
        if (self._check(TokenType.IDENTIFIER)
                and self.pos + 1 < len(self.tokens)
                and self.tokens[self.pos + 1].type == TokenType.EQ):
            name = self._advance().value
            self._advance()  # =
            value = self._parse_expression()
            return NamedArg(name=name, value=value)
        return self._parse_expression()

    # ================================================================
    # Token Helpers
    # ================================================================

    def _current(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return Token(TokenType.EOF, '', 0, 0)

    def _advance(self) -> Token:
        tok = self._current()
        self.pos += 1
        return tok

    def _check(self, token_type: TokenType) -> bool:
        return self._current().type == token_type

    def _check_any(self, *token_types: TokenType) -> bool:
        return self._current().type in token_types

    def _peek_is(self, token_type: TokenType) -> bool:
        """Check if the token after current is the given type."""
        if self.pos + 1 < len(self.tokens):
            return self.tokens[self.pos + 1].type == token_type
        return False

    def _expect(self, token_type: TokenType) -> Token:
        tok = self._current()
        if tok.type != token_type:
            raise ParseError(
                f"Expected {token_type.name}, got {tok.type.name} ({tok.value!r})",
                tok
            )
        return self._advance()

    def _expect_identifier_or_keyword(self) -> Token:
        """Expect an IDENTIFIER or accept a keyword token used as identifier."""
        tok = self._current()
        if tok.type == TokenType.IDENTIFIER:
            return self._advance()
        # Accept keywords as identifiers in certain contexts (e.g., @result, @prompt)
        keyword_as_ident = {
            TokenType.OUTPUT, TokenType.RESULT, TokenType.FORMAT,
            TokenType.MODEL, TokenType.VERSION, TokenType.SCHEMA,
            TokenType.ERROR, TokenType.STORE, TokenType.CACHE,
            TokenType.BUDGET, TokenType.LIMIT, TokenType.INPUT,
            TokenType.COMMIT, TokenType.GENERATE, TokenType.SELECT,
            TokenType.PROMPT, TokenType.ORDER, TokenType.FROM,
            TokenType.WHERE, TokenType.EXECUTE, TokenType.EXPLAIN,
            # SPL 2.0 additions
            TokenType.HALLUCINATION, TokenType.REFUSAL, TokenType.OVERFLOW,
            TokenType.ITERATIONS, TokenType.OTHERS, TokenType.TEMPERATURE,
            TokenType.WORKFLOW, TokenType.PROCEDURE, TokenType.EVALUATE,
            TokenType.RETRY, TokenType.RAISE, TokenType.CALL,
            TokenType.DEFAULT, TokenType.INTO,
        }
        if tok.type in keyword_as_ident:
            return self._advance()
        raise ParseError(
            f"Expected identifier, got {tok.type.name} ({tok.value!r})", tok
        )

    def _read_model_name(self) -> str:
        """Read a model name that may contain hyphens and numbers."""
        parts = []
        parts.append(self._expect(TokenType.IDENTIFIER).value)
        while self._check(TokenType.MINUS):
            self._advance()
            segment = ""
            tok = self._current()
            if tok.type == TokenType.IDENTIFIER:
                segment = self._advance().value
            elif tok.type == TokenType.INTEGER:
                segment = self._advance().value
                if self._check(TokenType.IDENTIFIER):
                    segment += self._advance().value
            elif tok.type == TokenType.FLOAT:
                segment = self._advance().value
            else:
                break
            parts.append(segment)
        return '-'.join(parts)
