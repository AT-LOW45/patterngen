# Patterngen

**RAG-based code generation that enforces your team's architectural decisions.**

Patterngen is a VS Code extension that generates boilerplate grounded in your own **Architecture Decision Records (ADRs)**. Instead of producing generic code, it retrieves the ADRs relevant to what you're building and instructs the LLM to follow them — so generated code matches your team's conventions for error handling, data fetching, response shapes, and whatever else you've documented.

## How it works

```
VS Code (generate boilerplate)
        │  prompt + language + selected code
        ▼
FastAPI backend  ──►  retrieve relevant ADRs (ChromaDB vector search)
        │                     │
        │  ◄──────────────────┘  full ADRs, in document order
        ▼
      LLM  ──►  code that follows the retrieved ADRs
        │
        ▼
   inserted at your cursor
```

The key idea is in retrieval: rather than returning scattered chunks, Patterngen identifies which **whole ADRs** are relevant to your request and feeds them to the LLM in full — so the concrete code examples in an ADR are never dropped. Irrelevant requests retrieve nothing, so the model just generates normally instead of being misled.

## Project structure

| Path | Stack | Role |
|------|-------|------|
| `rag/` | Python · FastAPI · LangChain · ChromaDB | Backend: indexes ADRs, retrieves context, generates code |
| `ui/` | Vue 3 · Vite · PrimeVue · TypeScript | Knowledge-base manager: upload, edit, delete ADRs |
| `src/` | TypeScript · VS Code API | The extension itself |

The Vue app is built to `ui/dist` and served by FastAPI at `/`, so the backend and knowledge-base UI run as a single server.

## Prerequisites

- **Python ≥ 3.13** and [`uv`](https://docs.astral.sh/uv/)
- **Node.js** (for the Vue knowledge-base UI)
- An **LLM API key** — Groq is the current default; the provider is configurable (see [llm_config.py](rag/config/llm_config.py))
- An **S3-compatible blob store** (for persisting raw ADR content) — for local development, use the bundled [MinIO](https://min.io/) setup, which only requires **Docker** (see step 2)

## Setup

### 1. Configure environment

Create a `.env` at the repo root (the `GROQ_API_KEY` below reflects the current default LLM provider — adjust if you configure a different one):

```env
GROQ_API_KEY=your_groq_key
API_ENDPOINT=http://localhost:8000
BLOB_ENDPOINT=http://localhost:9000
BLOB_ACCESS_KEY=...
BLOB_SECRET_KEY=...
BLOB_BUCKET=patterngen-docs
```

> The `BLOB_*` values are also consumed by the bundled MinIO setup (step 2): `BLOB_ACCESS_KEY`/`BLOB_SECRET_KEY` become MinIO's root credentials and `BLOB_BUCKET` is the bucket it creates. Use `http://localhost:9000` for `BLOB_ENDPOINT` when running MinIO locally. If you point at a managed S3-compatible store instead, set these to that store's values and skip step 2. Note: MinIO requires the access key to be **≥ 3 characters** and the secret key **≥ 8 characters**, or the container won't start.

### 2. Start the blob storage (MinIO via Docker)

The repo includes a [docker-compose.yml](docker-compose.yml) that runs a local MinIO server and creates the `BLOB_BUCKET` on startup. It reads credentials and the bucket name from the repo-root `.env` (step 1), so no secrets are hardcoded.

```bash
docker compose up -d      # start MinIO and create the bucket (pulls images on first run)
```

- **S3 API:** `http://localhost:9000` (matches `BLOB_ENDPOINT`)
- **Web console:** `http://localhost:9001` — log in with `BLOB_ACCESS_KEY` / `BLOB_SECRET_KEY` to browse stored ADRs

Objects persist in the `minio-data` Docker volume across restarts. Other commands:

```bash
docker compose down       # stop (data is preserved)
docker compose down -v    # stop and delete all stored objects
```

Skip this step if you're using a managed S3-compatible store; just point the `BLOB_*` values in `.env` at it.

### 3. Build the knowledge-base UI

```bash
cd ui
npm install
npm run build        # outputs to ui/dist, served by the backend
```

> `ui/.env` should set `VITE_API_ENDPOINT=http://localhost:8000` (same origin as the backend). Rebuild after changing it. For UI development with hot-reload, run `npm run dev` (Vite on :5173) instead.

### 4. Run the backend

```bash
cd rag
uv run python main.py    # FastAPI on http://localhost:8000 (reload enabled)
```

The knowledge-base UI is now available at `http://localhost:8000`.

### 5. Run the extension

Open the repo in VS Code and press **F5** to launch an Extension Development Host with Patterngen loaded.

## Usage

| Command | What it does |
|---------|--------------|
| **Patterngen: Generate Boilerplate** | Prompts for what to generate, detects the active file's language, optionally uses your selected code as context, and inserts ADR-grounded code at the cursor. |
| **Patterngen: Open Knowledge Base** | Opens the knowledge-base UI (the `ragEndpoint`) in your browser to manage ADRs. |

### Managing ADRs

Use the knowledge base UI to upload markdown ADRs, edit them in-place, and delete them. ADRs are chunked by markdown header and indexed for retrieval. To replace an existing ADR, re-upload it with the **same source name** — indexing is incremental and will swap the old chunks for the new ones.

## Configuration

This extension contributes the following setting:

- `patterngen.ragEndpoint` — URL of the RAG backend. Default: `http://localhost:8000`.

## Retrieval details

- **Embeddings:** `BAAI/bge-base-en-v1.5` (HuggingFace, local) — normalized, cosine distance, with a query-instruction prefix for asymmetric retrieval
- **Vector store:** ChromaDB (persisted to `rag/chroma_db`)
- **Chunking:** `MarkdownHeaderTextSplitter` on `#`/`##`/`###`, headers preserved, one chunk per section
- **Dedup:** LangChain incremental indexing with a SQLite record manager
- **LLM:** Groq `llama-3.3-70b-versatile` by default — configurable in [llm_config.py](rag/config/llm_config.py)
- **Retrieval:** ranks whole ADRs by their best-matching chunk, keeps those above a relevance threshold (capped), and returns each in full reassembled in document order

## Known limitations

- The relevance threshold (`0.5`) is calibrated against a small knowledge base; revisit it as you add more ADRs, since a stronger embedding model compresses scores into a narrower band.
- Retrieval still depends somewhat on phrasing. If quality degrades as the knowledge base grows, query enrichment (e.g. HyDE) or a hosted embedding model are the next levers.

## Development

- **Roadmap & tasks:** [GitHub Issues](https://github.com/AT-LOW45/patterngen/issues)
- [CHANGELOG.md](CHANGELOG.md) — user-facing release notes
