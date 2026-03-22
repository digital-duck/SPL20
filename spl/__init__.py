"""
SPL 2.0 - Structured Prompt Language for Agentic Workflow Orchestration

Extends SPL 1.0 with declarative primitives for agentic workflows:
EVALUATE, WHILE, DO/END, EXCEPTION, WORKFLOW, PROCEDURE, COMMIT, RETRY, RAISE.

Treats LLMs as generative knowledge bases with automatic token budget
optimization, built-in RAG, persistent memory, and now full procedural
control flow for multi-step agentic patterns.
"""

__version__ = "2.0.0"

from spl.lexer import Lexer
from spl.parser import Parser
from spl.analyzer import Analyzer
from spl.optimizer import Optimizer
from spl.executor import Executor, SPLResult, WorkflowResult
from spl.explain import explain_plan, explain_plans


def parse(source: str):
    """Parse SPL 2.0 source into AST."""
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    return parser.parse()


def validate(source: str):
    """Parse and semantically validate SPL 2.0 source."""
    ast = parse(source)
    analyzer = Analyzer()
    return analyzer.analyze(ast)


def optimize(source: str):
    """Parse, validate, and generate execution plans."""
    analysis = validate(source)
    optimizer = Optimizer()
    return optimizer.optimize(analysis)
