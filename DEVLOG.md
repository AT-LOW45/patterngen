# Dev Log

A dated, chronological record of development work on Patterngen. Newest entries first.
This is the internal engineering journal — for user-facing release notes see [CHANGELOG.md](CHANGELOG.md).

---

## 2026-07-05

### Create ADR page — full redesign
- Reworked [ui/src/pages/CreateAdrTemplatePage.vue](ui/src/pages/CreateAdrTemplatePage.vue) from a 4-step wizard into a **form + live markdown preview** split. All fields now use the shared `FormField` component; the right pane renders the assembled ADR (via `MdPreview`) live, in the same format as `docs/adr/`.
- **Code-capable sections:** Decision, a new Implementation section, and Notes use `md-editor-v3`'s `MdEditor` (trimmed toolbar, editor-only since the page has its own preview). Context/Consequences stay plain Textareas.
- **Custom sections:** users can add their own sections with a heading, body, and a per-section Plain-text / Rich-text toggle (`SelectButton`). Flows into the doc as `## {heading}`.
- **Design decision:** structured form for *create* (guided on-ramp for people unfamiliar with markdown); the *edit* page stays a single markdown editor. Format is a recommendation, not a requirement — arbitrary markdown still flows through upload + edit.

### Create ADR — persistence wired (no backend changes)
- `submitAdr` now assembles the fields into markdown, derives a `source` slug from id + title, and POSTs via `knowledgeBaseService.saveMarkdown` to the existing `/knowledge-base/index-document` endpoint — which already writes to blob storage + indexes. Added required-field validation (inline `FormField` errors + toast), loading state, and redirect to the list on success.
- Renamed `api-service` `reindexRecord` → `saveMarkdown` (serves both create and edit); updated the edit-page call site.
- Not yet verified against a running backend. `saveDraft` deferred.

### Collapsible sidebar
- Added a `useSidebar` composable (module-level shared `collapsed` ref, default collapsed). [Sidebar.vue](ui/src/components/layout/Sidebar.vue) animates w-16 ↔ w-64 with icon-only + tooltips when collapsed; [AppLayout.vue](ui/src/components/layout/AppLayout.vue) shifts content margin in step. In-memory only (resets on reload).

### Live preview scroll fix
- The preview pane wasn't scrolling — content past a certain point was clipped. Root cause: `md-editor`'s root is `height: 100%`, but the card had no bounded height, so the preview grew unbounded and `max-h` just clipped it. Fixed by making the preview card a `flex flex-col` bounded to `max-h-[calc(100vh-...)]`, with a `shrink-0` header and the preview as a `flex-1 min-h-0 overflow-y-auto` child so it scrolls internally while the card stays sticky.

### Cleanup — source generation moved to backend
- The frontend was slugifying the `source` key itself before submitting. Moved that logic server-side: `slugify` + `generate_source` in [knowledge_base_service.py](rag/service/knowledge_base_service.py) derive the key from the document's first `# ` H1 (which carries the id, e.g. `# ADR-003: …`).
- New `POST /knowledge-base` create endpoint derives the source, indexes, and returns `{ source, result }` (400 if no H1). `index-document` (explicit source) still serves the edit/reindex path.
- Frontend: removed the `slugify` helper; `submitAdr` calls the new `createDocument(content)` and uses the backend-returned source. `saveMarkdown` kept for edits. Resulting slug is unchanged — only where it's computed.

### Cleanup — auto-assigned ADR id
- The create form hardcoded `ADR-003`. Now the backend assigns it: `list_sources()` ([chroma_helper.py](rag/db/chroma_helper.py)) + `next_adr_id()` ([knowledge_base_service.py](rag/service/knowledge_base_service.py)) scan existing `adr-NNN` source prefixes and return max+1 (zero-padded), exposed via `GET /knowledge-base/next-id` (declared before `/{source}` so the static path wins).
- Frontend fetches it on mount; header shows "Assigning ID…" and **Create** is disabled until the id arrives; on fetch failure it stays disabled (avoids overwriting an existing id). Verified: with adr-001/002/003 indexed, next id = `ADR-004`.
- Known caveat: best-effort, not a reservation — concurrent creates could get the same id (ties into the overwrite-guard item).

### Cleanup — form validation via zod composable
- Replaced the create page's hand-rolled `validate()` + `errors` ref with the reusable `useZodValidation` composable ([ui/src/composables/useZodValidation.ts](ui/src/composables/useZodValidation.ts)) driven by a new [adrSchema.ts](ui/src/schemas/adrSchema.ts) (title/status/scope/decision required; extra form keys ignored).
- `submitAdr` calls `validate(form.value)` (composable owns the error toast); a `watch(form, simpleValidate, { deep: true })` re-validates live after the first failed submit so errors clear as fields are fixed. `FormField`s bind `validationErrors?.properties?.<field>?.errors`. Verified the treeifyError shape matches the binding path.
- Noted improvement for the shared composable (left unchanged to avoid cross-project divergence): guard against a null schema in `validate`/`simpleValidate` (currently can throw). Optional: auto-`watch` a schema `Ref`; derive `ZodErrorTree` from `ReturnType<typeof z.treeifyError>`.

### Cleanup — extracted create-page logic into a composable
- The create page's `<script setup>` had grown to ~200 lines. Moved all state/behaviour into [useCreateAdr.ts](ui/src/composables/useCreateAdr.ts) — form state + types, validation, markdown assembly, dark-mode tracking, id fetch, live re-validation, and all actions (`addAlternative`, `add/removeCustomSection`, `saveDraft`, `submitAdr`), plus the static UI config (`statusOptions`, `formatOptions`, `mdToolbars`).
- [CreateAdrTemplatePage.vue](ui/src/pages/CreateAdrTemplatePage.vue) is now template + a single `useCreateAdr()` destructure (~20-line script). Pure extraction — no behaviour change, type-checks clean. Bonus: concentrates ADR-structure logic in one file, which will help when configurable formats land.

### Cleanup — enforce router → service → db/storage layering
- The `knowledge_base` router was calling `chroma_helper` (db) and `blob_storage` (storage) directly, and even orchestrated two-store deletes in the controller — breaking the layering stated in CLAUDE.md.
- Moved it behind the service: added `list_documents`, `get_document_raw`, `get_document_chunks`, `delete_document`, `clear_documents` to [knowledge_base_service.py](rag/service/knowledge_base_service.py) (delete/clear now own the vector-store + blob orchestration), plus a `get_chunks` helper in [chroma_helper.py](rag/db/chroma_helper.py) to keep db access in the db layer.
- [knowledge_base.py](rag/router/knowledge_base.py) now imports only from `service` (+ exception/fastapi/schema) — verified no `db.`/`storage.` imports. Exception→404 mapping stays in the controller (HTTP concern). Handlers renamed to `*_endpoint`.
- Also gave the draft router a [draft_service.py](rag/service/draft_service.py) (owns the JSON (de)serialization; router just passes dicts). Verified **all three routers** (knowledge_base, draft, boilerplate) are now free of direct `db.`/`storage.` imports — layering consistent end to end.

### Cleanup — useZodValidation composable
- Replaced the deprecated `ZodTypeAny` (only present in zod v4's `compat` shim: `export { ZodType as ZodTypeAny }`) with the modern **`z.ZodType`** base type, in both the `ZodErrorTree` constraint and the composable generic.
- Added a **null-schema guard** to `validate`/`simpleValidate` (capture `currentSchema.value` to a const, bail early — `validate` returns `true`, `simpleValidate` no-ops), removing the latent NPE and giving clean TS narrowing. Type-checks + lints clean.
- Note: this composable is shared across the user's projects — both fixes are worth backporting.

### Draft support (single overwritable version per draft) — end to end
- **Backend:** drafts stored as opaque form JSON at `drafts/<id>.json` in blob storage (never indexed). Dedicated [router/draft.py](rag/router/draft.py) (`/knowledge-base/drafts`) → [draft_service.py](rag/service/draft_service.py) (owns JSON (de)serialization) → blob helpers. CRUD: list, `PUT/GET/DELETE /{id}`. Included before `knowledge_base` router so it wins over `/{source}`.
- **Frontend:** separate `draftService` object in [api-service.ts](ui/src/api-service.ts) (mirrors the backend split). [useCreateAdr.ts](ui/src/composables/useCreateAdr.ts) tracks a `draftId` (UUID generated on first save, independent of the ADR id since next-id isn't reserved). Resume via `?draft=<id>` (loads on mount); saving overwrites the same id.
- **Publish consumes the draft:** after a successful create, `deleteDraft(draftId)` removes it from storage so it drops out of the list (best-effort — a cleanup failure doesn't fail the already-created ADR).
- **List page** ([KnowledgeBaseListPage.vue](ui/src/pages/KnowledgeBaseListPage.vue)) merges drafts with published ADRs, adds a **Type** column (Draft tag vs "Published"), resumes drafts on row-click, and routes delete to the right service.
- Type-checks clean. Not yet exercised against a running MinIO — needs a live round-trip check.

### Create page — unsaved-changes guard
- Added dirty-tracking + a leave warning to [useCreateAdr.ts](ui/src/composables/useCreateAdr.ts): snapshots the form as a pristine baseline after load (new id / resumed draft) and after each save; `isDirty` = form ≠ baseline.
- `onBeforeRouteLeave` blocks in-app navigation while dirty and shows a modal ([CreateAdrTemplatePage.vue](ui/src/pages/CreateAdrTemplatePage.vue)) warning that leaving discards progress, with **Save as draft** (saves → proceeds) and **Cancel** (stays). A `beforeunload` listener covers tab-close/refresh via the native prompt. Publish sets a bypass flag so creating an ADR doesn't trigger the warning.
- Interpretation: warns only when there's actual unsaved content — a pristine, untouched new form (just the auto-assigned id) does not warn.
- Dialog has three actions: **Leave without saving** (discards, proceeds via the bypass flag), **Cancel** (stays), **Save as draft** (saves → proceeds).

### Planned feature — AI ADR quality review (design, not built)
Advisory quality gate that reviews an ADR *before* submission and flags issues, so users can fix or submit anyway. Motivation: garbage-in-garbage-out — ADR quality gates generation quality downstream (cf. the self-contradictory ADR-001 the generator faithfully copied, and the mangled ADR-002 that wrecked retrieval).

Key design decisions from the discussion:
- **Split the checks by nature — don't LLM everything:**
  - *Deterministic (plain code, no LLM):* missing required sections (parse `##` headers for Title/Scope/Decision/etc.), word-count / length limit, malformed/unclosed code fences. Cheap, instant, reliable, free.
  - *Semantic (LLM earns its keep):* off-topic/irrelevant text, incoherent or self-contradictory decisions, code-sample plausibility. Scope "bad code" narrowly → syntactic plausibility + matches the stated language, NOT deep code-quality opinions.
- **Advisory, never blocking** — flag issues, let the user "Submit anyway". Consistent with recommend-not-require.
- **No numeric score** — it implies false precision and LLMs aren't stable scorers. Emit a coarse verdict (Good / Needs work / Poor) + a findings list `{ severity, section, message }`.
- **Applies to create AND upload** — the create form already enforces structure; the real value is the upload path (arbitrary `.md`) and free-text/custom sections.

Proposed architecture:
- New endpoint `POST /knowledge-base/review` — takes markdown, runs deterministic checks + one Groq call (reuse `config/llm_config.py`) with **structured JSON output**, returns `{ verdict, findings[], wordCount, missingSections[] }`. Findings are ephemeral (not persisted).
- Frontend: a "Check quality" action (and/or run on Create) → findings dialog → **Fix** or **Submit anyway**.

MVP: deterministic checks + a single LLM semantic pass returning `{ verdict, findings[] }`, advisory only. Defer the numeric score and deep code judgment.

### Planned feature — configurable ADR formats (idea only, not designed yet)
Today the ADR format is hardcoded to the author's own (Status/Scope/Context/Decision/Implementation/Consequences). Different teams use different ADR formats, so the system should **understand a team's own format** when indexing and when generating code. Idea: a new page to define/manage their ADR format.

Rough shape / things to figure out later:
- A format = a set of section definitions (name, required?, description, code-capable?). One source of truth that drives multiple places:
  - **Create page** — render fields dynamically from the format instead of the hardcoded sections.
  - **AI quality review** — the "required sections" check reads from the team's format, not a fixed list.
  - **Indexing** — chunking already splits generically on `##` headers, so arbitrary formats already chunk; the real work is tagging which sections matter (e.g. Decision/Implementation) for retrieval.
  - **Generation** — the boilerplate prompt should know which sections carry the actionable decisions/code for that team's format.
- Open questions: scoping (per team / per workspace / per knowledge base?); where the format config lives (backend db/blob/config); migration of existing ADRs; whether formats are picked per-ADR or set once per team.
- Connects to the existing custom-sections feature on the create page (that's a lightweight, per-ADR version of this).

Not being tackled yet — parked alongside the quality-review feature.

### What to do next
- **Planned features (parked, not started):** (1) AI ADR quality review — suggested start is deterministic structural checks, then the LLM semantic pass; (2) configurable ADR formats per team. See the two design notes above.
- **Verify the create flow end-to-end** — largely confirmed: `adr-003-api-authentication-strategy` is indexed from the UI test. Still worth a spot-check that it renders in the list and is retrievable via a generate-boilerplate prompt.
- **Overwrite guard** — creating with an existing `source` silently reindexes/replaces it (same as edit); now more relevant since the auto-id is best-effort and two same-title ADRs collide. Decide whether to warn before overwrite.
- **Test the draft flow against MinIO** — save → resume → publish (draft deleted) → delete-from-list, end to end.
- **Git hygiene** — `rag/chroma_db/` and `rag/record_manager.db` are tracked and churn binary diffs every commit; `.gitignore` + `git rm --cached` them.
- **Lower-priority backlog** — persist sidebar collapsed state (localStorage); backend health-check on extension activate; `.env` path inconsistency in [rag/storage/blob_storage.py](rag/storage/blob_storage.py) (loads `rag/.env`, which doesn't exist — works only by accident).

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
