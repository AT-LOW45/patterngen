from exception.document_not_found_error import DocumentNotFoundError
from fastapi.responses import JSONResponse
from fastapi import HTTPException, UploadFile, File, APIRouter
from schema.boilerplate_schema import CreateDocumentRequest
from service.knowledge_base_service import (
    index_document as kb_index_document,
    generate_source,
    next_adr_id,
    list_documents,
    get_document_raw,
    get_document_chunks,
    delete_document,
    clear_documents,
)

router = APIRouter(prefix="/knowledge-base", tags=["Knowledge Base"])


@router.post("")
async def create_document_endpoint(request: CreateDocumentRequest):
    """Create a new record. The source key is derived server-side from the
    document's H1 title — callers do not supply it."""
    source = generate_source(request.content)
    if not source:
        raise HTTPException(
            status_code=400,
            detail="Could not derive a source: the document needs a top-level '# ' title.",
        )

    result = await kb_index_document(request.content, source)
    return JSONResponse(content={"source": source, "result": result})


@router.post("/index-document")
async def index_document_endpoint(file: UploadFile = File(...), source: str = ""):
    content = await file.read()
    text = content.decode("utf-8")
    source_name = source or file.filename

    if not source_name:
        return JSONResponse(
            status_code=400, content={"error": "source name is required"}
        )

    result = await kb_index_document(text, source_name)
    return JSONResponse(content={"result": result})


@router.get("/next-id")
async def next_id_endpoint():
    """The next sequential ADR id to pre-fill the create form. Best-effort — not a
    reservation, so concurrent creates could collide (see overwrite handling)."""
    return JSONResponse(content={"id": next_adr_id()})


@router.get("/{source}/raw")
async def get_document_raw_endpoint(source: str):
    try:
        content = get_document_raw(source)
    except DocumentNotFoundError:
        raise HTTPException(status_code=404, detail=f"Document '{source}' not found")
    return JSONResponse(content={"source": source, "content": content})


@router.get("")
async def list_documents_endpoint():
    return JSONResponse(content={"sources": list_documents()})


@router.get("/{source}")
async def get_document_content_endpoint(source: str):
    chunks = get_document_chunks(source)
    return JSONResponse(
        content={"source": source, "chunks": chunks, "chunk_count": len(chunks)}
    )


@router.delete("/{source}")
async def delete_document_endpoint(source: str):
    delete_document(source)
    return JSONResponse(content={"deleted": source})


@router.delete("")
async def clear_knowledge_base_endpoint():
    return JSONResponse(content={"deleted": clear_documents()})
