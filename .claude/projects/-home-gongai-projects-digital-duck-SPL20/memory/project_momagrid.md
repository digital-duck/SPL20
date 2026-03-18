---
name: Momagrid integration context
description: Momagrid is a decentralized AI inference runtime at /home/gongai/projects/digital-duck/momagrid - Go-based hub-and-spoke architecture with HTTP API for task submission, used as SPL 2.0's distributed execution backend
type: project
---

Momagrid is the user's other major project — a decentralized AI inference grid written in Go. arXiv paper submitted March 2026.

**Architecture**: Hub-and-spoke. Hub dispatches tasks to agents (worker nodes running Ollama). Multiple hubs can peer together.

**Key API endpoints for SPL 2.0 integration**:
- `POST /tasks` — Submit single task (model, prompt, system, max_tokens, temperature, min_tier, min_vram_gb, timeout_s, priority). Returns 202 with task_id.
- `GET /tasks/{task_id}` — Poll for result (state: PENDING → DISPATCHED → IN_FLIGHT → COMPLETE/FAILED)
- `POST /jobs` — Long-running tasks with deadline, webhook notification, retries
- `GET /agents` — Online agents with tier, models, TPS, VRAM info
- `GET /cluster/status` — Peer hub capabilities

**SPL already exists in Momagrid**: The momagrid repo has its own SPL parser (Go) with `ON GRID` clause and CTE parallel execution. SPL 2.0 (Python) is the next-gen version.

**Integration path**: Create a `momagrid` LLM adapter in SPL 2.0 that submits tasks via HTTP to a Momagrid hub, polls for results, and returns them. The IR JSON output can also be used for batch job submission.

**Why:** SPL 2.0 is the language layer; Momagrid is the execution layer. Connecting them enables distributed LLM inference from SPL programs.

**How to apply:** When building the momagrid adapter, use httpx (like openrouter/ollama adapters), target `POST /tasks` + `GET /tasks/{id}` polling loop, and support `ON GRID` syntax or `--adapter momagrid` CLI flag.
