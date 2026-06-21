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

### Investigated — SQLRecordManager / langchain-classic (no action)
- Questioned whether `SQLRecordManager` (imported from `langchain_classic.indexes` in [rag/db/chroma_helper.py](rag/db/chroma_helper.py)) is on a deprecation path. Checked installed versions (langchain 1.3.1, core 1.4.0, classic 1.0.7) and the official v1 migration guide.
- Findings: `langchain-classic` is **not deprecated** — it's a deliberate permanent home for functionality "outside the focus of standard interfaces and agents." The whole indexing API (`index()`, `RecordManager`, `SQLRecordManager`) was *moved* there in v0.3→v1, not retired. Our `langchain_classic.indexes` import is the officially correct, current path.
- There is no more-modern replacement: the record-manager + `index(cleanup="incremental")` pattern is still the supported way to do dedup/incremental indexing. `DocumentIndex` is an alternative storage target, not a RecordManager replacement. `InMemoryRecordManager` (core) is non-persistent, so not viable here.
- Conclusion: no change needed. Revisit only if LangChain announces a deprecation. Refs: [v1 migration guide](https://docs.langchain.com/oss/python/migrate/langchain-v1), [langchain_classic indexes reference](https://reference.langchain.com/python/langchain-classic/indexes).

### Embedding model upgrade — MiniLM → bge-base-en-v1.5
- Swapped the embedding model in [rag/db/chroma_helper.py](rag/db/chroma_helper.py) from `all-MiniLM-L6-v2` to `BAAI/bge-base-en-v1.5` (free, local, no API/cost). Added normalized embeddings, cosine distance on the Chroma collection, and bge's query-instruction prefix for asymmetric (short query → long passage) retrieval.
- bge is 768-dim vs MiniLM's 384, so the Chroma collection + record manager had to be rebuilt from scratch. Backed up both ADRs first, wiped `chroma_db`/`record_manager.db`, reindexed. Also promoted both ADRs to source-of-truth files under [docs/adr/](docs/adr/).
- **Results (same scoring harness):** the false-negative is fixed — "create a hook to fetch products" went from **0.010 → 0.658** and now retrieves the right ADR. bge also *corrected* a MiniLM ranking error: on "handle errors in an API route", MiniLM ranked the frontend ADR above the error ADR; bge ranks the error ADR first (0.680 vs 0.669). Genuine queries now rank the correct ADR top; junk (cookies, weather) returns empty.
- **Recalibrated threshold** against 10 test queries (5 genuine, 5 junk): bge compresses scores into a high band, so the old `0.0` was meaningless. Genuine floor 0.567, junk ceiling 0.415 → set `score_threshold = 0.5` (≈0.085 margin both sides). Far more robust than the prior single-point calibration.

### Reusable threshold calibration tool
- Added [rag/scripts/calibrate_threshold.py](rag/scripts/calibrate_threshold.py) — the standing way to recalibrate `score_threshold`. Run `cd rag && uv run python scripts/calibrate_threshold.py`. It scores editable GENUINE vs JUNK query lists, reports the genuine floor / junk ceiling / gap, and suggests the midpoint threshold (warns if the bands overlap, which means the embedding model can't discriminate).
- **Re-run it after** changing the embedding model, adding a batch of ADRs, or if the generator starts ignoring relevant ADRs / pulling in irrelevant ones. Keep the GENUINE/JUNK lists representative of the real knowledge base.

### Notes / known limitations
- The `0.0` threshold is calibrated against only 2 ADRs — recheck as the knowledge base grows.
- Root cause of fragile retrieval is the embedding model (`all-MiniLM-L6-v2`): small, general-purpose, weak on code/architecture vocabulary. Durable fix is a stronger/code-aware embedding model and/or query enrichment (e.g. HyDE) — not threshold tuning.
- PROGRESS.md is a throwaway artifact from Claude Cowork; this DEVLOG is the source of truth going forward.
