# Testing spl-go with the Cookbook

`cookbook_catalog_go.json` mirrors the standard catalog but runs every recipe through the `spl-go` binary (zero-dependency Go runtime). Use it to catch regressions and find missing functionality before they reach production.

## Prerequisites

- `spl-go` binary on your PATH (built from `~/projects/digital-duck/SPL.go/`)
- Ollama running locally (`ollama serve`)

```bash
# Verify spl-go is reachable
spl-go version

# Rebuild if needed  (~/.local/bin/spl-go is a symlink — just rebuild in place)
cd ~/projects/digital-duck/SPL.go && go build -o spl-go .
```

## Run all active recipes against spl-go

```bash
cd ~/projects/digital-duck/SPL20

# Sequential (recommended for first pass — shows live output)
python cookbook/run_all.py --catalog-file cookbook/cookbook_catalog_go.json 2>&1 | tee cookbook/out/run_all_go_$(date +%Y%m%d_%H%M%S).md


python cookbook/run_all.py --catalog-file cookbook/cookbook_catalog_go.json \
    --ids "4, 14, 17, 25, 06, 37, 13, 36, 41–44, 47–49" \
    2>&1 | tee cookbook/out/run_all_go_$(date +%Y%m%d_%H%M%S).md

# Override model
python cookbook/run_all.py --catalog-file cookbook/cookbook_catalog_go.json --model llama3.2

# Run specific recipes by ID
python cookbook/run_all.py --catalog-file cookbook/cookbook_catalog_go.json --ids 01,02,05,07
```

## Browse the go catalog

```bash
# Full table
python cookbook/run_all.py --catalog-file cookbook/cookbook_catalog_go.json --catalog

# Filter by category
python cookbook/run_all.py --catalog-file cookbook/cookbook_catalog_go.json --catalog --category agentic

# What's disabled and why
python cookbook/run_all.py --catalog-file cookbook/cookbook_catalog_go.json --catalog --status disabled
```

## Disabled recipes and why

| Recipes | Reason | Status |
|---|---|---|
| 06, 37 | `claude_cli` adapter | **Unblocked ✓ 2026-04-18** — `claude_cli` adapter exists; use `--adapter claude_cli --allowed-tools WebSearch` |
| 13, 36, 41–44, 47–49 | `--tools` Python plugin | **Unblocked ✓ 2026-04-18** — `--tools path/to/tools.py` loads `@spl_tool` functions via subprocess |
| 22 | Shell script calls `spl2` internally | Still blocked — rewrite `text2spl_demo.sh` for spl-go |
| 38, 39, 40 | Bedrock / Vertex / Azure adapters not in spl-go | Still blocked — port cloud-provider adapters |

### Using `--tools`

```bash
# Recipe 36 — Tool-Use (deterministic math via Python, narrative via LLM)
spl-go run cookbook/36_tool_use/tool_use.spl \
    --adapter ollama --model gemma3 \
    --tools cookbook/36_tool_use/tools.py \
    sales="1200,1450,1380,1600,1750,1900"

# Recipe 13 — Map-Reduce
spl-go run cookbook/13_map_reduce/map_reduce.spl \
    --adapter ollama --model gemma3 \
    --tools cookbook/13_map_reduce/tools.py

# Recipe 41 — Human Steering
spl-go run cookbook/41_human_steering/human_steering.spl \
    --adapter ollama --model gemma3 \
    --tools cookbook/41_human_steering/tools.py
```

The `--tools` flag loads any Python file with `@spl_tool`-decorated functions.
Each function becomes a CALL-able tool in the SPL workflow — dispatched before
procedures and LLM fallback. Python itself is invoked as a subprocess; no Python
interpreter is embedded in the Go binary.

### Using `claude_cli` adapter

```bash
# Recipe 37 — Headline News (claude_cli, no WebSearch needed)
spl-go run cookbook/37_headline_news/headline_news.spl \
    --adapter claude_cli --model claude-opus-4-6 \
    topic="artificial intelligence"

# Recipe 06 — ReAct Agent (claude_cli + WebSearch tool)
spl-go run cookbook/06_react_agent/react_agent.spl \
    --adapter claude_cli --model claude-sonnet-4-6 \
    --allowed-tools WebSearch \
    --tools cookbook/06_react_agent/tools.py \
    country="France"
```

## Logs

Each recipe writes a `-go.md` suffixed log to `~/.spl/logs/` (e.g. `hello-ollama-20260413-103000-go.md`), making it easy to distinguish from Python runtime logs in the same directory.

## Comparing runtimes side by side

```bash
# Run the same recipe on both runtimes, then diff the logs
spl     run ./cookbook/01_hello_world/hello.spl --adapter ollama
spl-go  run ./cookbook/01_hello_world/hello.spl --adapter ollama

ls -lt ~/.spl/logs/hello-* | head -4
```
