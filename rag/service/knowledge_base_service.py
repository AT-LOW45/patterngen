# service/knowledge_base_service.py
import re

from langchain_core.documents import Document
from langchain_core.indexing import IndexingResult
from db.chroma_helper import add_to_index, list_sources
from storage.blob_storage import upload_to_blob


def next_adr_id() -> str:
    """Next sequential ADR id (e.g. 'ADR-004') based on existing source keys like 'adr-003-...'."""
    highest = 0
    for source in list_sources():
        match = re.match(r"adr-0*(\d+)", source)
        if match:
            highest = max(highest, int(match.group(1)))
    return f"ADR-{highest + 1:03d}"


def slugify(value: str) -> str:
    """Turn a title into a URL/key-safe slug, e.g. 'ADR-003: API Auth' -> 'adr-003-api-auth'."""
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def generate_source(content: str) -> str:
    """
    Derive a stable source key from the document's first H1 heading.
    Returns "" if the document has no H1 (caller decides how to handle).
    """
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return slugify(stripped[2:])
    return ""


async def index_document(content: str, source: str) -> IndexingResult:
    # store original in blob storage
    upload_to_blob(content, source)

    # index chunks in vector store
    document = Document(page_content=content, metadata={"source": source})
    result = add_to_index([document], source)

    return result