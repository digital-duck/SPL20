"""SPL 2.0 Token types and Token dataclass.

Extends SPL 1.0 tokens with new keywords for agentic workflow orchestration.
"""

from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    # === SPL 1.0 Keywords (unchanged) ===
    PROMPT = auto()
    WITH = auto()
    BUDGET = auto()
    TOKENS = auto()
    USING = auto()
    MODEL = auto()
    SELECT = auto()
    AS = auto()
    LIMIT = auto()
    WHERE = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    IN = auto()
    ORDER = auto()
    BY = auto()
    ASC = auto()
    DESC = auto()
    GENERATE = auto()
    OUTPUT = auto()
    CREATE = auto()
    FUNCTION = auto()
    RETURNS = auto()
    EXPLAIN = auto()
    EXECUTE = auto()
    PARAMS = auto()
    STORE = auto()
    RESULT = auto()
    CACHE = auto()
    FOR = auto()
    FROM = auto()
    TEMPERATURE = auto()
    FORMAT = auto()
    BEGIN = auto()
    COMMIT = auto()
    ROLLBACK = auto()
    TRANSACTION = auto()
    ON = auto()
    ERROR = auto()
    AUTO_COMPRESS = auto()
    COMPRESSION_STRATEGY = auto()
    SCHEMA = auto()
    VERSION = auto()
    REFRESH = auto()
    EVERY = auto()
    MATERIALIZED = auto()
    GRID = auto()
    VRAM = auto()

    # === SPL 2.0 New Keywords ===
    EVALUATE = auto()
    WHEN = auto()
    THEN = auto()
    WHILE = auto()
    DO = auto()
    END = auto()
    EXCEPTION = auto()
    WORKFLOW = auto()
    INPUT = auto()
    PROCEDURE = auto()
    RETRY = auto()
    RAISE = auto()
    OTHERWISE = auto()
    INTO = auto()
    CALL = auto()
    DEFAULT = auto()
    SET = auto()

    # Security / Accounting / Labels keywords
    SECURITY = auto()
    ACCOUNTING = auto()
    CLASSIFICATION = auto()
    LABELS = auto()

    # Exception type keywords (can also be identifiers)
    HALLUCINATION = auto()
    REFUSAL = auto()
    OVERFLOW = auto()
    ITERATIONS = auto()
    OTHERS = auto()

    # === Literals ===
    INTEGER = auto()
    FLOAT = auto()
    STRING = auto()
    IDENTIFIER = auto()

    # === Operators ===
    DOT = auto()
    COMMA = auto()
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    EQ = auto()
    NEQ = auto()
    GT = auto()
    LT = auto()
    GTE = auto()
    LTE = auto()
    STAR = auto()
    PLUS = auto()
    MINUS = auto()
    AT = auto()
    ASSIGN = auto()     # :=
    COLON = auto()      # :
    PERCENT = auto()    # %

    # === Delimiters ===
    SEMICOLON = auto()
    DOLLAR_DOLLAR = auto()

    # === Special ===
    EOF = auto()


# Map keyword strings to token types (case-insensitive)
KEYWORDS: dict[str, TokenType] = {
    # SPL 1.0 keywords
    "prompt": TokenType.PROMPT,
    "with": TokenType.WITH,
    "budget": TokenType.BUDGET,
    "tokens": TokenType.TOKENS,
    "using": TokenType.USING,
    "model": TokenType.MODEL,
    "select": TokenType.SELECT,
    "as": TokenType.AS,
    "limit": TokenType.LIMIT,
    "where": TokenType.WHERE,
    "and": TokenType.AND,
    "or": TokenType.OR,
    "not": TokenType.NOT,
    "in": TokenType.IN,
    "order": TokenType.ORDER,
    "by": TokenType.BY,
    "asc": TokenType.ASC,
    "desc": TokenType.DESC,
    "generate": TokenType.GENERATE,
    "output": TokenType.OUTPUT,
    "create": TokenType.CREATE,
    "function": TokenType.FUNCTION,
    "returns": TokenType.RETURNS,
    "explain": TokenType.EXPLAIN,
    "execute": TokenType.EXECUTE,
    "params": TokenType.PARAMS,
    "store": TokenType.STORE,
    "result": TokenType.RESULT,
    "cache": TokenType.CACHE,
    "for": TokenType.FOR,
    "from": TokenType.FROM,
    "temperature": TokenType.TEMPERATURE,
    "format": TokenType.FORMAT,
    "begin": TokenType.BEGIN,
    "commit": TokenType.COMMIT,
    "rollback": TokenType.ROLLBACK,
    "transaction": TokenType.TRANSACTION,
    "on": TokenType.ON,
    "error": TokenType.ERROR,
    "auto_compress": TokenType.AUTO_COMPRESS,
    "compression_strategy": TokenType.COMPRESSION_STRATEGY,
    "schema": TokenType.SCHEMA,
    "version": TokenType.VERSION,
    "refresh": TokenType.REFRESH,
    "every": TokenType.EVERY,
    "materialized": TokenType.MATERIALIZED,
    "grid": TokenType.GRID,
    "vram": TokenType.VRAM,
    # SPL 2.0 new keywords
    "evaluate": TokenType.EVALUATE,
    "when": TokenType.WHEN,
    "then": TokenType.THEN,
    "while": TokenType.WHILE,
    "do": TokenType.DO,
    "end": TokenType.END,
    "exception": TokenType.EXCEPTION,
    "workflow": TokenType.WORKFLOW,
    "input": TokenType.INPUT,
    "procedure": TokenType.PROCEDURE,
    "retry": TokenType.RETRY,
    "raise": TokenType.RAISE,
    "otherwise": TokenType.OTHERWISE,
    "into": TokenType.INTO,
    "call": TokenType.CALL,
    "default": TokenType.DEFAULT,
    "set": TokenType.SET,
    "security": TokenType.SECURITY,
    "accounting": TokenType.ACCOUNTING,
    "classification": TokenType.CLASSIFICATION,
    "labels": TokenType.LABELS,
    "hallucination": TokenType.HALLUCINATION,
    "refusal": TokenType.REFUSAL,
    "overflow": TokenType.OVERFLOW,
    "iterations": TokenType.ITERATIONS,
    "others": TokenType.OTHERS,
}


@dataclass(frozen=True)
class Token:
    type: TokenType
    value: str
    line: int
    column: int

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r}, {self.line}:{self.column})"
