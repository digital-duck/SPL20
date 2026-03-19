"""Natural language to SPL 2.0 source code compiler.

Uses an LLM adapter to convert natural language task descriptions
into valid SPL 2.0 source code.
"""

from __future__ import annotations

from spl2.adapters.base import LLMAdapter
from spl2.lexer import Lexer, LexerError
from spl2.parser import Parser, ParseError
from spl2.analyzer import Analyzer, AnalysisError


SPL2_SYSTEM_PROMPT = """\
You are an expert SPL 2.0 code generator. SPL 2.0 (Structured Prompt Language) is \
a SQL-inspired declarative language for orchestrating LLM interactions. Given a \
natural language description of a task, you produce valid SPL 2.0 source code.

Return ONLY the raw SPL 2.0 code. Do not include markdown fences, explanations, \
or commentary.

== SPL 2.0 SYNTAX REFERENCE ==

--- PROMPT statement ---
A single LLM call that selects context and generates output:

PROMPT <name> [WITH BUDGET <n> TOKENS] [USING MODEL '<model>']
SELECT <expr> [AS <alias>] [LIMIT <n> TOKENS], ...
[FROM <source>]
[WHERE <condition>]
[ORDER BY <field> ASC|DESC]
GENERATE <function>(<args>) [WITH TEMPERATURE <t>] [WITH OUTPUT BUDGET <n> TOKENS]
[STORE IN <target>];

--- WORKFLOW statement ---
Multi-step orchestration with control flow:

WORKFLOW <name>
  INPUT @<var> <TYPE>, ...
  OUTPUT @<var> <TYPE>
DO
  -- body statements
END;

--- CREATE FUNCTION ---
Define reusable functions:

CREATE FUNCTION <name>(<param> <TYPE>, ...) RETURNS <TYPE> AS $$
  <body>
$$;

--- Key constructs inside WORKFLOW bodies ---

Variable assignment:
  @<var> := <expression>;

Generate into variable:
  GENERATE <function>(<args>) INTO @<var> [USING MODEL '<model>'];

Commit output:
  COMMIT @<var>;

Conditional branching:
  EVALUATE
    WHEN <condition> THEN
      <statements>
    WHEN <condition> THEN
      <statements>
    OTHERWISE
      <statements>
  END;

Looping:
  WHILE <condition> DO
    <statements>
  END;

Call a sub-workflow or procedure:
  CALL <name>(<args>);

Exception handling:
  DO
    <statements>
  EXCEPTION
    WHEN <ExceptionType> THEN
      <statements>
  END;

RAISE;   -- re-raise an exception
RETRY;   -- retry the current DO block

--- Condition syntax ---
Deterministic:  @var > 0.8, @var = 'done', @count < 5
Semantic:       'the text is high quality', 'user intent is a question'

--- Exception types ---
HallucinationDetected, RefusalToAnswer, ContextLengthExceeded,
ModelOverloaded, QualityBelowThreshold, MaxIterationsReached,
BudgetExceeded, NodeUnavailable

--- Built-in functions ---
summarize(), translate(), classify(), extract_entities(), sentiment(),
answer(), rewrite(), generate_code()
Arguments can be positional or named: function(arg1, arg2, style='formal')

--- Types ---
TEXT, NUMBER, BOOLEAN, LIST, JSON

== EXAMPLES ==

Example 1 -- Simple summarisation prompt:

PROMPT summarize_doc WITH BUDGET 2000 TOKENS
SELECT @document AS content LIMIT 1500 TOKENS
GENERATE summarize(content) WITH OUTPUT BUDGET 500 TOKENS;

Example 2 -- Multi-step review workflow with quality loop:

WORKFLOW review_agent
  INPUT @draft TEXT
  OUTPUT @final TEXT
DO
  @quality := 0.0;
  @current := @draft;
  WHILE @quality < 0.8 DO
    GENERATE rewrite(@current, style='improved') INTO @current;
    GENERATE sentiment(@current) INTO @quality;
  END;
  @final := @current;
  COMMIT @final;
END;

Example 3 -- Classification with exception handling:

WORKFLOW safe_classify
  INPUT @text TEXT
  OUTPUT @label TEXT
DO
  DO
    GENERATE classify(@text) INTO @label;
    COMMIT @label;
  EXCEPTION
    WHEN HallucinationDetected THEN
      @label := 'unknown';
      COMMIT @label;
    WHEN ModelOverloaded THEN
      RETRY;
  END;
END;

Example 4 -- Translation prompt with model selection:

PROMPT translate_email USING MODEL 'claude-sonnet'
SELECT @email AS source LIMIT 1000 TOKENS,
       'French' AS target_language
GENERATE translate(source, target_language) WITH OUTPUT BUDGET 1200 TOKENS;
"""


_MODE_INSTRUCTIONS = {
    "prompt": (
        "Generate a single PROMPT statement. Do not use WORKFLOW or CREATE FUNCTION "
        "unless absolutely necessary for a helper."
    ),
    "workflow": (
        "Generate a WORKFLOW statement with full control flow. You may also emit "
        "CREATE FUNCTION statements if helper functions are needed."
    ),
    "auto": (
        "Decide whether the task is best expressed as a single PROMPT statement or "
        "a multi-step WORKFLOW (possibly with helper functions). Use PROMPT for "
        "simple one-shot tasks and WORKFLOW for anything that requires iteration, "
        "branching, or multiple generation steps."
    ),
}


class Text2SPL:
    """Compile natural language descriptions into SPL 2.0 source code."""

    def __init__(self, adapter: LLMAdapter, max_retries: int = 2) -> None:
        self.adapter = adapter
        self.max_retries = max_retries

    async def compile(self, description: str, mode: str = "auto") -> str:
        """Convert a natural language task description into SPL 2.0 source code.

        Args:
            description: A plain-English description of the desired behaviour,
                e.g. "summarize this document" or "build a review agent that
                refines text until quality > 0.8".
            mode: One of ``"prompt"`` (emit a PROMPT statement),
                ``"workflow"`` (emit a WORKFLOW), or ``"auto"`` (let the LLM
                choose the best form).

        Returns:
            A string containing valid SPL 2.0 source code.

        Raises:
            ValueError: If *mode* is not one of the accepted values.
        """
        if mode not in _MODE_INSTRUCTIONS:
            raise ValueError(
                f"Invalid mode {mode!r}. Must be one of: "
                f"{', '.join(sorted(_MODE_INSTRUCTIONS))}"
            )

        user_prompt = (
            f"Task: {description}\n\n"
            f"Mode instruction: {_MODE_INSTRUCTIONS[mode]}\n\n"
            "Generate the SPL 2.0 code now."
        )

        result = await self.adapter.generate(
            prompt=user_prompt,
            system=SPL2_SYSTEM_PROMPT,
            temperature=0.3,
        )

        spl_code = self._strip_fences(result.content.strip())

        # Compile-validate-retry loop: if the generated code is invalid,
        # feed the error back to the LLM for correction
        for attempt in range(self.max_retries):
            valid, message = self.validate_output(spl_code)
            if valid:
                break
            # Ask the LLM to fix the error
            fix_prompt = (
                f"The following SPL 2.0 code has an error:\n\n"
                f"```\n{spl_code}\n```\n\n"
                f"Error: {message}\n\n"
                f"Fix the error and return only the corrected SPL 2.0 code. "
                f"Do not include markdown fences or explanations."
            )
            fix_result = await self.adapter.generate(
                prompt=fix_prompt,
                system=SPL2_SYSTEM_PROMPT,
                temperature=0.2,
            )
            spl_code = self._strip_fences(fix_result.content.strip())

        return spl_code

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @staticmethod
    def validate_output(spl_source: str) -> tuple[bool, str]:
        """Parse and analyse *spl_source* to check if it is valid SPL 2.0.

        Returns:
            A ``(valid, message)`` tuple.  When ``valid`` is ``True``,
            *message* is ``"OK"`` (possibly followed by warnings).
            When ``valid`` is ``False``, *message* describes the first
            error encountered.
        """
        # Stage 1: Lexing
        try:
            lexer = Lexer(spl_source)
            tokens = lexer.tokenize()
        except LexerError as exc:
            return False, f"Lexer error: {exc}"

        # Stage 2: Parsing
        try:
            parser = Parser(tokens)
            program = parser.parse()
        except ParseError as exc:
            return False, f"Parse error: {exc}"

        # Stage 3: Semantic analysis
        try:
            analyzer = Analyzer()
            analysis = analyzer.analyze(program)
        except AnalysisError as exc:
            return False, f"Analysis error: {exc}"

        # Collect warnings, if any
        if analysis.warnings:
            warnings_text = "; ".join(w.message for w in analysis.warnings)
            return True, f"OK (warnings: {warnings_text})"

        return True, "OK"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _strip_fences(text: str) -> str:
        """Remove markdown code fences if the LLM wrapped its output."""
        lines = text.splitlines()
        if not lines:
            return text

        # Strip leading ```spl or similar
        if lines[0].strip().startswith("```"):
            lines = lines[1:]
        # Strip trailing ```
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        return "\n".join(lines)
