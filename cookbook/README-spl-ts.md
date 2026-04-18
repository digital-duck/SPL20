# Testing spl-ts with the Cookbook

`cookbook_catalog_ts.json` mirrors the standard catalog but runs every recipe through the `spl-ts` binary (TypeScript runtime). Use it to catch regressions and find missing functionality before they reach production.

## Prerequisites

- `spl-ts` binary on your PATH (`~/.local/bin/spl-ts` is a symlink into `~/projects/digital-duck/SPL.ts/`)
- Ollama running locally (`ollama serve`)

```bash
# Verify spl-ts is reachable
spl-ts --version

# Rebuild if needed  (~/.local/bin/spl-ts is a symlink — just rebuild in place)
cd ~/projects/digital-duck/SPL.ts && npm run build
```

## Run all active recipes against spl-ts

```bash
cd ~/projects/digital-duck/SPL20

# Sequential (recommended for first pass — shows live output)
python cookbook/run_all.py --catalog-file cookbook/cookbook_catalog_ts.json 2>&1 | tee cookbook/out/run_all_ts_$(date +%Y%m%d_%H%M%S).md


python cookbook/run_all.py --catalog-file cookbook/cookbook_catalog_ts.json \
    --ids "04,06,12,13,14,18,20,25,26,28-33,36,37,41-44,47-49" \
    2>&1 | tee cookbook/out/run_all_ts_$(date +%Y%m%d_%H%M%S).md


# Override model
python cookbook/run_all.py --catalog-file cookbook/cookbook_catalog_ts.json --model llama3.2

# Run specific recipes by ID
python cookbook/run_all.py --catalog-file cookbook/cookbook_catalog_ts.json --ids 01,02,05,07
```

## Browse the ts catalog

```bash
# Full table
python cookbook/run_all.py --catalog-file cookbook/cookbook_catalog_ts.json --catalog

# Filter by category
python cookbook/run_all.py --catalog-file cookbook/cookbook_catalog_ts.json --catalog --category agentic

# What's disabled and why
python cookbook/run_all.py --catalog-file cookbook/cookbook_catalog_ts.json --catalog --status disabled
```

## Disabled recipes and why

| Recipes | Reason | Unblocked by |
|---|---|---|
| 08 | `rag.query()` not yet implemented | Implement RAG built-in in spl-ts |
| 19 | `memory.get/set` not yet implemented | Implement memory built-ins in spl-ts |
| 22 | Shell script calls `spl2` internally | Rewrite `text2spl_demo.sh` for spl-ts |
| 38, 39, 40 | Bedrock / Vertex / Azure adapters not in spl-ts | Port cloud-provider adapters to TypeScript |

Previously disabled and now re-enabled: 04 (`PROMPT...GENERATE...INTO` fix), 06/37 (`claude_cli` adapter), 13/36/41–44/47–49 (`--tools` Python bridge).

## Logs

Each recipe writes a `-ts.md` suffixed log to `~/.spl/logs/` (e.g. `hello-ollama-20260418-103000-ts.md`), making it easy to distinguish from Python and Go runtime logs in the same directory.

## Comparing runtimes side by side

```bash
# Run the same recipe on all three runtimes, then compare logs
spl     run ./cookbook/01_hello_world/hello.spl --adapter ollama
spl-go  run ./cookbook/01_hello_world/hello.spl --adapter ollama
spl-ts  run ./cookbook/01_hello_world/hello.spl --adapter ollama

ls -lt ~/.spl/logs/hello-* | head -6
```
