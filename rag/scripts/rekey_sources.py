"""
One-off migration: re-key existing records from the old number-in-key format
(adr-001-error-handling) to the new title-only key (error-handling).

Run once per device that has existing data, after pulling the source-key decoupling
(issue #3). Records already in the new format are left untouched, so it's safe to
re-run. Unlike seed_adrs.py this is NON-destructive — it preserves records that
aren't in docs/adr (e.g. ADRs created via the UI).

Prereqs: MinIO running + repo-root .env with BLOB_* creds.

Usage (from the rag/ directory):
    uv run python scripts/rekey_sources.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.chroma_helper import list_sources  # noqa: E402
from service.knowledge_base_service import (  # noqa: E402
    generate_source,
    get_document_raw,
    index_document,
    delete_document,
)


async def main() -> None:
    sources = list_sources()
    if not sources:
        print("No records to migrate.")
        return

    migrated = 0
    for source in sources:
        content = get_document_raw(source)  # blob still keyed by the old source
        new_source = generate_source(content)  # title-only under the new rules

        if not new_source:
            print(f"  ! {source} — no H1 title, skipped")
            continue
        if new_source == source:
            print(f"  = {source} — already title-only")
            continue

        # Index under the new key first, then drop the old — a failure mid-way leaves a
        # recoverable duplicate rather than losing the record.
        await index_document(content, new_source)
        delete_document(source)
        migrated += 1
        print(f"  ✓ {source}  ->  {new_source}")

    print(f"Done — {migrated} record(s) re-keyed.")


if __name__ == "__main__":
    asyncio.run(main())
