# SPL 2.0 (Structured Prompt Language)

SPL 2.0 is a declarative, SQL-inspired language for orchestrating agentic LLM workflows. It extends SPL 1.0 with procedural control flow, making it "PL/SQL for LLMs."

## Project Overview

- **Purpose**: To provide a declarative alternative to imperative Python frameworks (like LangChain or CrewAI) for building LLM agents.
- **Key Concepts**:
    - `PROMPT`: Single-step LLM query.
    - `WORKFLOW`: Multi-step agentic orchestration.
    - `PROCEDURE`: Reusable parameterized sub-workflows.
    - `EVALUATE`: Semantic (LLM-judged) or deterministic branching.
    - `WHILE`: Iterative refinement loops.
    - `GENERATE ... INTO`: Capture LLM output into variables.
- **Architecture**:
    - **Lexer/Parser**: Converts `.spl` files into an AST.
    - **Analyzer**: Performs semantic validation.
    - **Optimizer**: Handles token budget allocation and workflow planning.
    - **Executor**: Runs the workflow against various LLM backends.
    - **Adapters**: Pluggable backends for providers like OpenAI, Anthropic, Google (Gemini/Vertex), AWS Bedrock, Ollama, and Momagrid (decentralized grid).

## Building and Running

### Setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

### Key CLI Commands
- `spl run <file.spl>`: Execute an SPL program.
- `spl validate <file.spl>`: Check syntax and semantic correctness.
- `spl explain <file.spl>`: Show the execution plan without calling an LLM.
- `spl text2spl "<description>"`: Compile natural language into SPL code.
- `spl adapters`: List all available LLM backends.

### Testing
```bash
pytest tests/
```

## Development Conventions

- **Language**: Python 3.11+.
- **CLI Framework**: `click`.
- **Testing**: `pytest` with `pytest-asyncio`.
- **Typing**: Uses Python type hints extensively.
- **Adapter Pattern**: New LLM providers should be added as `LLMAdapter` subclasses in `spl/adapters/`.
- **Exception Handling**: Use the custom SPL exceptions (e.g., `HallucinationDetected`, `RefusalToAnswer`) defined in `spl/executor.py`.

## Directory Structure Highlights

- `spl/`: Core engine source code.
    - `ast_nodes.py`: AST dataclass definitions.
    - `executor.py`: The heart of the runtime.
    - `adapters/`: Individual LLM provider implementations.
- `cookbook/`: A collection of 48+ reference implementations for agentic patterns (RAG, ReAct, Self-Refine, etc.).
- `docs/`: Design documents and user guides.
- `tests/`: Comprehensive test suite covering all phases of the compiler and runtime.
