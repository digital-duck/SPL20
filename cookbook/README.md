# SPL 2.0 Cookbook

Ready-to-run recipes demonstrating SPL 2.0 capabilities. Each recipe is self-contained.

## Prerequisites

```bash
conda create -n spl2 python=3.11
conda activate spl2

pip install -e ".[dev]"          # install spl
# pip install httpx                # for ollama/openrouter/momagrid adapters

ollama pull gemma3               # at least one model
ollama serve                     # start ollama (if not running)
```

## Batch Runner — `run_all.py`

`run_all.py` uses a Click CLI with three subcommands: `list`, `catalog`.

### Run recipes

```bash
cd ~/projects/digital-duck/SPL20

# Run all active recipes (sequential, ollama adapter)
python cookbook/run_all.py \
  --adapter ollama --model gemma3 \
  2>&1 | tee cookbook/out/run_all_$(date +%Y%m%d_%H%M%S).md

# Override adapter and model
python cookbook/run_all.py  --adapter ollama --model gemma3

# Run specific recipes or ranges
python cookbook/run_all.py  --ids "04,10,23-35"
python cookbook/run_all.py  --ids "04,10,25,26,29,30,32,33"

# Run recipes in a category
python cookbook/run_all.py  --category agentic
```

### Run on momagrid (parallel mode)

When `--adapter momagrid` is set, all recipes are submitted **concurrently** so the hub
dispatcher sees multiple tasks in the queue at once and distributes work across GPU nodes:

```bash
export MOMAGRID_HUB_URL=http://192.168.1.10:9000

# All active recipes in parallel
python cookbook/run_all.py  --adapter momagrid --model llama3.2

# Limit concurrency (default: one worker per recipe)
python cookbook/run_all.py  --adapter momagrid --model llama3.2 --workers 4

# Subset in parallel
python cookbook/run_all.py  --adapter momagrid --ids "01-10,13"
```

In parallel mode, each recipe logs to its own file under `<recipe_dir>/`. Completion
messages print as recipes finish; a summary table appears at the end.

### Running from a client machine (laptop, no GPU required)

The machine submitting recipes does **not** need to be a grid agent — it is a pure client.
It submits SPL tasks to the hub over HTTP; the hub dispatches them to GPU nodes.

**Step 1 — Verify hub is reachable**

```bash
curl http://192.168.0.235:9000/agents
```

You should see a JSON list of online agents. If this fails, check that you are on the same
LAN as the hub machine (duck, 192.168.0.235).

**Step 2 — Install dependencies (first time only)**

```bash
cd ~/projects/digital-duck/SPL20
pip install -e .       # install spl package
pip install httpx      # momagrid adapter HTTP client
```

If the repo is not cloned yet:

```bash
git clone https://github.com/digital-duck/SPL20 ~/projects/digital-duck/SPL20
cd ~/projects/digital-duck/SPL20
pip install -e .
pip install httpx
```

**Step 3 — Run all recipes**

```bash
bash cookbook/run_cookbook_on_momagrid.sh
```

The script exports `MOMAGRID_HUB_URL=http://192.168.0.235:9000` and runs all 37 active
recipes with `--workers 10`. Output is saved to `cookbook/out/run_all_<timestamp>-momagrid.md`.

Or run directly:

```bash
export MOMAGRID_HUB_URL=http://192.168.0.235:9000
python cookbook/run_all.py  --adapter momagrid --workers 10 2>&1 \
  | tee cookbook/out/run_laptop_$(date +%Y%m%d_%H%M%S).md
```

`--workers 10` controls how many recipes the client submits concurrently to the hub.
The hub's own dispatch across GPU nodes is independent of this value.

---

### Hub URL resolution (no env var needed)

The momagrid adapter resolves the hub URL in this order:

1. `hub_url=` constructor argument
2. `MOMAGRID_HUB_URL` environment variable
3. `~/.igrid/config.yaml` → `hub.urls[0]`  ← auto-populated by `mg join`
4. `http://localhost:9000` (last resort)

After running `mg join <hub-url>` on any machine, subsequent `spl run --adapter momagrid`
calls will find the hub automatically without needing to export `MOMAGRID_HUB_URL`.

### LAN cluster — tuning agent participation

The hub dispatches tasks by **tier first** (GOLD > SILVER > BRONZE), then by least active
tasks. With `--max-concurrent 3` (the default) and three GOLD nodes, the grid has 9 GOLD
slots — a SILVER node only receives work when all 9 GOLD slots are busy.

**To give lower-tier nodes more work, choose one:**

**Option A — Promote the node's tier** (use when the hardware is comparable):
```bash
# PostgreSQL hub
psql momagrid -c "UPDATE agents SET tier='GOLD' WHERE name='goose';"

# SQLite hub
sqlite3 .igrid/hub.sqlite3 "UPDATE agents SET tier='GOLD' WHERE name='goose';"
```
The change takes effect immediately; no hub restart required.

**Option B — Increase max-concurrent slots per agent** (use when you want all nodes busier):
```bash
# Restart the hub with more slots per agent
mg hub up --max-concurrent 5   # 4 nodes × 5 = 20 total slots
```
With 20 slots and 10 workers the SILVER node starts filling in much sooner.

**Reference — LAN 4-node cluster (duck/cat/dog/goose)**

| Node  | GPU           | VRAM  | Tier   |
|-------|---------------|-------|--------|
| duck  | GTX 1080 Ti   | 11 GB | GOLD   |
| cat   | GTX 1080 Ti   | 11 GB | GOLD   |
| dog   | GTX 1080 Ti   | 11 GB | GOLD   |
| goose | RTX 4060      |  8 GB | SILVER |

Hub: `http://192.168.0.235:9000` (duck machine, PostgreSQL backend)

---

### Hub-to-Hub Peering over the Internet (Pinggy)

By default a Momagrid hub is only reachable inside its LAN.
[Pinggy](https://pinggy.io) creates a temporary public HTTPS tunnel to a local port — no account required, no binary to install — so two users on different LANs can test hub-to-hub peering without opening firewall ports.

**Scenario:** Bob and Alice each run their own LAN Momagrid hub and want to peer the two grids.

#### Step 1 — Start the local hub

Both Bob and Alice must have their hub running before opening the tunnel:

```bash
mg hub up
```

#### Step 2 — Each user opens a Pinggy tunnel

Bob (hub on port 9000):
```bash
ssh -p 443 -R0:localhost:9000 a.pinggy.io
```

Alice (same command):
```bash
ssh -p 443 -R0:localhost:9000 a.pinggy.io
```

Each session prints a public URL in the terminal, e.g.:
```
https://qgzqm-99-111-153-200.run.pinggy-free.link
```

Bob and Alice exchange their URLs (chat, Slack, etc.).

#### Step 3 — Point the SPL client at the Pinggy URL

To submit recipes through the tunnel rather than the LAN IP, set `MOMAGRID_HUB_URL` to your own Pinggy URL:

```bash
# Bob
export MOMAGRID_HUB_URL=https://qgzqm-99-111-153-200.run.pinggy-free.link

# Alice
export MOMAGRID_HUB_URL=https://abcde-11-22-33-44.run.pinggy-free.link
```

Quick smoke test — does the hub respond over the tunnel?

```bash
curl $MOMAGRID_HUB_URL/health
```

#### Step 4 — Register the peer hub

Bob registers Alice's public URL:
```bash
mg peer add https://abcde-11-22-33-44.run.pinggy-free.link
```

Alice registers Bob's:
```bash
mg peer add https://qgzqm-99-111-153-200.run.pinggy-free.link
```

Verify both sides see each other:
```bash
mg peer list
```

Expected output (Bob's side):
```
This hub: <bob-hub-id>
  <alice-hub-id>  https://abcde-11-22-33-44.run.pinggy-free.link  [online]
```

#### Step 5 — Run a recipe across the peered grids

Bob submits recipes to his hub; the hub forwards overflow to Alice's:
```bash
python cookbook/run_all.py --adapter momagrid --ids "01-05" --workers 4
```

Or target a single recipe:
```bash
spl run cookbook/47_arxiv_morning_brief/arxiv_morning_brief.spl \
    --adapter momagrid \
    --param urls='["https://arxiv.org/pdf/2501.12948"]'
```

Alice does the same against her own `MOMAGRID_HUB_URL`.

#### Notes

| Topic | Detail |
|---|---|
| Tunnel lifetime | Free Pinggy tunnels stay open as long as the `ssh` session is alive; close the terminal to tear it down |
| Port | Change `-R0:localhost:9000` if your hub uses a different port |
| Keepalive | Add `-o "ServerAliveInterval 30"` to prevent idle disconnects |
| Persistent URL | A paid Pinggy account gives a fixed subdomain — useful if you want a stable peer URL across sessions |

---

### Browse recipes

```bash
# Brief list
python cookbook/run_all.py list
python cookbook/run_all.py list --category agentic
python cookbook/run_all.py list --status new

# Full catalog table
python cookbook/run_all.py catalog
python cookbook/run_all.py catalog --category reasoning
python cookbook/run_all.py catalog --status approved
```

## Code-RAG

Run 
```bash
spl code-rag parse-log cookbook/out/run_all_20260320_052826.md 
```
once the run finishes to capture all 30 new  (prompt, SPL) pairs into Code-RAG       



## Recipes

Status: `✓` done · `-` parser/runtime pending · `todo` not yet written

### Tier 1 — Core SPL (Language Fundamentals)

| # | Recipe | Script | Description | Status |
|---|--------|--------|-------------|--------|
| 01 | Hello World | `hello.spl` | Minimal SPL program — verify spl + Ollama work | ✓ |
| 02 | Ollama Proxy | `proxy.spl` | General-purpose LLM query — proxy any Ollama model | ✓ |
| 03 | Multilingual | `multilingual.spl` | Greet in any language — parametric `lang` demo | ✓ |
| 04 | Model Showdown | `showdown.spl` | Same prompt to multiple models via CTEs, compare output | ✓ |
| 05 | Self-Refine | `self_refine.spl` | Iterative improvement: draft → critique → refine loop | ✓ |
| 06 | ReAct Agent | `react_agent.spl` | Reasoning + Acting loop with tool-call pattern | ✓ |
| 07 | Safe Generation | `safe_generation.spl` | Exception handling for production LLM safety | ✓ |
| 08 | RAG Query | `rag_query.spl` | Retrieval-augmented generation over indexed documents | - |
| 09 | Chain of Thought | `chain.spl` | Multi-step reasoning: Research → Analyze → Summarize | ✓ |
| 10 | Batch Test | `batch_test.sh` | Automated testing of multiple .spl scripts across models | ✓ |

### Tier 2 — Agentic Patterns

| # | Recipe | Script | Description | Status |
|---|--------|--------|-------------|--------|
| 11 | Debate Arena | `debate.spl` | Adversarial debate between two LLM personas with a judge | ✓ |
| 12 | Plan and Execute | `plan_execute.spl` | Planner decomposes task into steps, executor runs each one | ✓ |
| 13 | Map-Reduce | `map_reduce.spl` | Split large docs into chunks, summarize each, combine results | ✓ |
| 14 | Multi-Agent | `multi_agent.spl` | Researcher → Analyst → Writer collaboration via PROCEDURE | ✓ |
| 15 | Code Review | `code_review.spl` | Multi-pass review: security, performance, style, bugs | ✓ |
| 16 | Reflection | `reflection.spl` | Meta-cognitive loop: solve → reflect → correct until confident | ✓ |
| 17 | Tree of Thought | `tree_of_thought.spl` | Explore multiple reasoning paths, score and pick the best | ✓ |
| 18 | Guardrails | `guardrails.spl` | Input/output safety pipeline with PII detection and filtering | ✓ |
| 19 | Memory Chat | `memory_chat.spl` | Persistent memory across conversations via memory.get/set | - |
| 20 | Ensemble Voting | `ensemble.spl` | Generate multiple answers, score and vote for consensus | ✓ |
| 21 | Multi-Model Pipeline | `multi_model.spl` | Per-step model selection with GENERATE...USING MODEL and quality loop | ✓ |
| 22 | Text2SPL Demo | `text2spl_demo.sh` | Natural language to SPL 2.0 compiler — prompt, workflow, and auto modes | - |

### Tier 3 — SPL Language Features (Completeness)

| # | Recipe | Script | Key Feature | Status |
|---|--------|--------|-------------|--------|
| 23 | Structured Output | `structured_output.spl` | `CREATE FUNCTION` with JSON schema — extract typed data from free text | ✓ |
| 24 | Few-Shot Prompting | `few_shot.spl` | Gold-standard examples embedded in `SELECT` context | ✓ |
| 25 | Nested Procedures | `nested_procs.spl` | `PROCEDURE` calling `PROCEDURE` — deep composability | ✓ |
| 26 | Prompt A/B Test | `ab_test.spl` | CTEs + `EVALUATE` scoring — compare two prompt variants, pick winner | ✓ |

### Tier 4 — Real-World Pipelines

| # | Recipe | Script | Domain | Status |
|---|--------|--------|--------|--------|
| 27 | Data Extraction | `data_extraction.spl` | Pull structured fields from messy text (names, dates, amounts) | ✓ |
| 28 | Customer Support Triage | `support_triage.spl` | Classify → route → draft response in one workflow | ✓ |
| 29 | Meeting Notes → Actions | `meeting_actions.spl` | Transcript in, structured TODO list + owners out | ✓ |
| 30 | Code Generator + Tests | `code_gen.spl` | Generate function, then generate its unit tests | ✓ |
| 31 | Sentiment Pipeline | `sentiment.spl` | Batch sentiment over a list, aggregate trends | ✓ |

### Tier 5 — Advanced Agentic Patterns

| # | Recipe | Script | Pattern | Status |
|---|--------|--------|---------|--------|
| 32 | Socratic Tutor | `socratic_tutor.spl` | Ask guiding questions rather than giving answers directly | ✓ |
| 33 | Interview Simulator | `interview_sim.spl` | Two-persona structured Q&A with evaluation | ✓ |
| 34 | Progressive Summarizer | `progressive_summary.spl` | Layered summary: sentence → paragraph → page | ✓ |
| 35 | Hypothesis Tester | `hypothesis.spl` | Generate hypothesis → design test → evaluate evidence | ✓ |

### Tier 6 — Tool Connectors (Multimodal)

Tool connectors mirror the LLM adapter pattern. `backend` is to connectors what `model` is to adapters.
Local and online backends are interchangeable — declared in `config.yaml` or overridden via `--connector`.

```yaml
# .spl/config.yaml
connectors:
  pdf:
    backend: pymupdf          # local default
    # backend: adobe-api      # online alternative
  transcribe:
    backend: whisper          # local
    model: base
    # backend: assemblyai     # online alternative
  tts:
    backend: piper            # local
    # backend: elevenlabs     # online alternative
```

```bash
# CLI override — same pattern as --adapter
spl run script.spl --connector pdf=pymupdf
spl run script.spl --connector transcribe=assemblyai
```

| # | Recipe | Script | Connector | Status |
|---|--------|--------|-----------|--------|
| 36 | PDF Analyst | `pdf_analyst.spl` | `tool.pdf_to_md` — ingest PDF, extract insights | todo |
| 37 | Audio → Action Items | `audio_actions.spl` | `tool.transcribe` — meeting recording → structured tasks | todo |


## Quick Smoke Test

```bash
# Parse all recipes (no LLM needed)
for f in cookbook/*/*.spl; do spl validate "$f"; done

# Run hello world with echo adapter (no Ollama needed)
spl run cookbook/01_hello_world/hello.spl

# Run with Ollama
spl run cookbook/01_hello_world/hello.spl --adapter ollama


```


### Test — Hello World

```bash
spl run cookbook/01_hello_world/hello.spl --adapter ollama
```

```
============================================================
Model: gemma3
Tokens: 38 in / 45 out
Latency: 1200ms
------------------------------------------------------------
Hello! I'm your friendly SPL 2.0 assistant. SPL (Structured Prompt Language)
is a declarative language for orchestrating LLM workflows — think SQL for AI.
============================================================
```


### Test — Ollama Proxy (any model, any prompt)

```bash
spl run cookbook/02_ollama_proxy/proxy.spl --adapter ollama --model gemma3 prompt="Explain quantum computing"
```

```
============================================================
Model: gemma3
Tokens: 44 in / 824 out
Latency: 12965ms
------------------------------------------------------------
Okay, let's break down quantum computing...
============================================================
```


### Test — Multilingual Greeting

```bash
spl run cookbook/03_multilingual/multilingual.spl --adapter ollama user_input="hello wen" lang="Chinese"
```

```
============================================================
Model: gemma3
Tokens: 54 in / 21 out
Latency: 440ms
------------------------------------------------------------
你好，文！ (Nǐ hǎo, Wén!)

(Hello, Wen!)
============================================================
```


### Test — Model Showdown (compare models)

```bash
bash cookbook/04_model_showdown/showdown.sh "What is the meaning of life?"
```


### Test — Self-Refining Agent

```bash
spl run cookbook/05_self_refine/self_refine.spl --adapter ollama --model gemma3 task="Write a haiku about coding"
```


### Test — Multi-Model Pipeline (per-step model selection)

```bash
spl run cookbook/21_multi_model_pipeline/multi_model.spl --adapter ollama topic="climate change"
```

This recipe showcases `GENERATE ... USING MODEL` — each step can target a different model within the same workflow.


### Test — Text2SPL Demo (NL → SPL compiler)

```bash
bash cookbook/22_text2spl_demo/text2spl_demo.sh
```

Demonstrates the `spl text2spl` / `spl text2spl` command: natural language descriptions compiled into valid SPL 2.0 code with automatic validation.


### Test — Batch Test (all models x all recipes)

```bash
bash cookbook/10_batch_test/batch_test.sh
```
