# service/knowledge_base_service.py
import re

from langchain_core.documents import Document
from langchain_core.indexing import IndexingResult
from db.chroma_helper import add_to_index, list_sources, get_chunks, delete_from_index
from storage.blob_storage import upload_to_blob, get_from_blob, delete_from_blob


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


def list_documents() -> list[str]:
    """All indexed source keys."""
    return list_sources()


def get_document_raw(source: str) -> str:
    """The canonical markdown for a source (raises DocumentNotFoundError if missing)."""
    return get_from_blob(source)


def get_document_chunks(source: str) -> list[str]:
    """The indexed chunk texts for a source."""
    return get_chunks(source)


def delete_document(source: str) -> None:
    """Remove a document from both the vector store and blob storage."""
    delete_from_index(source, clear_key=True)
    delete_from_blob(source)


def clear_documents() -> list[str]:
    """Delete every document from both stores; returns the sources removed."""
    sources = list_sources()
    for source in sources:
        delete_document(source)
    return sources