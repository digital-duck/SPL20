# Testing spl-go with the Cookbook

`cookbook_catalog_go.json` mirrors the standard catalog but runs every recipe through the `spl-go` binary (zero-dependency Go runtime). Use it to catch regressions and find missing functionality before they reach production.

## Prerequisites

- `spl-go` binary on your PATH (built from `~/projects/digital-duck/SPL.go/`)
- Ollama running locally (`ollama serve`)

```bash
# Verify spl-go is reachable
spl-go version

# Rebuild if needed
cd ~/projects/digital-duck/SPL.go && go build -o spl-go . && cp spl-go ~/bin/
```

## Run all active recipes against spl-go

```bash
cd ~/projects/digital-duck/SPL20

# Sequential (recommended for first pass — shows live output)
python cookbook/run_all.py --catalog-file cookbook/cookbook_catalog_go.json 2>&1 | tee cookbook/out/run_all_go_$(date +%Y%m%d_%H%M%S).md

# Override model
python cookbook/run_all.py --catalog-file cookbook/cookbook_catalog_go.json -m llama3.2

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

| Recipes | Reason | Unblocked by |
|---|---|---|
| 06, 37 | `claude_cli` adapter not in spl-go | Port claude_cli adapter to Go |
| 13, 36, 41–44, 47–49 | `--tools` (Python plugin) not in spl-go | Implement `--tools` flag in Go runner |
| 22 | Shell script calls `spl2` internally | Rewrite `text2spl_demo.sh` for spl-go |

## Logs

Each recipe writes a `-go.md` suffixed log to `~/.spl/logs/` (e.g. `hello-ollama-20260413-103000-go.md`), making it easy to distinguish from Python runtime logs in the same directory.

## Comparing runtimes side by side

```bash
# Run the same recipe on both runtimes, then diff the logs
spl     run ./cookbook/01_hello_world/hello.spl --adapter ollama
spl-go  run ./cookbook/01_hello_world/hello.spl --adapter ollama

ls -lt ~/.spl/logs/hello-* | head -4
```
