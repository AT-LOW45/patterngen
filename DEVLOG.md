# Dev Log

A dated, chronological record of development work on Patterngen. Newest entries first.
This is the internal engineering journal — for user-facing release notes see [CHANGELOG.md](CHANGELOG.md).

---

## 2026-06-21

### Boilerplate generation — template crash fix
- Fixed a bug in [rag/service/boilerplate_service.py](rag/service/boilerplate_service.py) where the user's selected code was interpolated into the prompt *template string* via an f-string. Any selection containing `{`/`}` (i.e. almost all real code) was parsed as a template variable and crashed before reaching the LLM.
- Selection is now passed as a runtime value (`selection_note`) at invoke time, where braces are treated as literal text. Also removed a dead `selection_context` variable that no template placeholder consumed.

### Retrieval rework — full-ADR assembly
- Rewrote `search_index` in [rag/db/chroma_helper.py](rag/db/chroma_helper.py). Old behaviour: return the top-k matching *chunks*. Problem: prose chunks (Context/Decision) outrank code chunks, so the actual code examples were being dropped from context.
- New behaviour: rank *ADRs* (by their best-matching chunk), keep those above a score threshold (capped at `max_sources`), and return each relevant ADR *in full*, reassembled in document order. Irrelevant queries return empty so the LLM generates normally instead of being fed noise.
- Added `chunk_index` metadata at split time so an ADR can be reassembled in order.

### ADR content cleanup
- ADR-002 was badly mangled in the store (30 fragmented chunks, lost spaces, `## •`/`## 1` artifacts). Rewrote it as clean markdown at [docs/adr/adr-002-frontend-state-management.md](docs/adr/adr-002-frontend-state-management.md) → splits into 7 clean chunks. Reindexed both ADRs so they carry `chunk_index`.

### Threshold calibration
- Tuned `score_threshold` against observed relevance scores: started 0.15 → 0.1 → **0.0**. A task-phrased query ("create a hook to fetch products") scored only 0.010 for the relevant ADR and was being filtered out as a false negative. Junk/vague queries score *negative*, so 0.0 cleanly separates genuine matches from noise.
- Verified end-to-end: error-handling and products-hook prompts now generate ADR-compliant code (custom exception classes + `{data,error}` shape; TanStack Query + `apiFetcher` respectively).

### Notes / known limitations
- The `0.0` threshold is calibrated against only 2 ADRs — recheck as the knowledge base grows.
- Root cause of fragile retrieval is the embedding model (`all-MiniLM-L6-v2`): small, general-purpose, weak on code/architecture vocabulary. Durable fix is a stronger/code-aware embedding model and/or query enrichment (e.g. HyDE) — not threshold tuning.
- PROGRESS.md is a throwaway artifact from Claude Cowork; this DEVLOG is the source of truth going forward.
