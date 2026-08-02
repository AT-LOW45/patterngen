"""
Seed the knowledge base from docs/adr/*.md — the git-tracked source of truth.

Overwrite semantics: clears ALL existing records (vector store + blob), then indexes
every ADR file fresh. Run this after pulling on a new device to rebuild its local
stores, or whenever you want the stores to exactly match docs/adr.

Prereqs: MinIO running (docker compose up) and a repo-root .env with BLOB_* creds.

Usage (from the rag/ directory):
    uv run python scripts/seed_adrs.py
"""

import asyncio
import sys
from pathlib import Path

# allow `python scripts/seed_adrs.py` from the rag/ dir
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from service.knowledge_base_service import (  # noqa: E402
    index_document,
    generate_source,
    clear_documents,
)

ADR_DIR = Path(__file__).resolve().parent.parent.parent / "docs" / "adr"


async def main() -> None:
    files = sorted(ADR_DIR.glob("*.md"))
    if not files:
        print(f"No ADRs found in {ADR_DIR}")
        return

    # Overwrite: wipe everything first so the stores end up exactly matching docs/adr.
    removed = clear_documents()
    print(f"Cleared {len(removed)} existing record(s): {removed}")

    for path in files:
        content = path.read_text(encoding="utf-8")
        source = generate_source(content)
        if not source:
            print(f"  ! skipped {path.name} — no '# ' H1 title to derive a source from")
            continue
        result = await index_document(content, source)
        print(result)
        print(f"  ✓ seeded {source}  ({path.name})")

    print(f"Done — {len(files)} ADR file(s) processed.")


if __name__ == "__main__":
    asyncio.run(main())
