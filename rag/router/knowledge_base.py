from db.chroma_helper import delete_from_index
from fastapi.responses import JSONResponse
from fastapi import UploadFile, File, APIRouter
from db.chroma_helper import vector_store
from storage.blob_storage import delete_from_blob, get_from_blob
from service.knowledge_base_service import index_document as kb_index_document

router = APIRouter(prefix="/knowledge-base", tags=["Knowledge Base"])

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


@router.get("/{source}/raw")
async def get_document_raw(source: str):
    content = get_from_blob(source)
    return JSONResponse(content={"source": source, "content": content})


@router.get("")
async def get_knowledge_base():
    results = vector_store.get()

    # extract unique sources from metadata
    sources = list(
        set(metadata.get("source", "unknown") for metadata in results["metadatas"])
    )

    return JSONResponse(content={"sources": sources})


@router.get("/{source}")
async def get_document_content(source: str):
    results = vector_store.get(where={"source": source})

    chunks = results["documents"]

    return JSONResponse(
        content={"source": source, "chunks": chunks, "chunk_count": len(chunks)}
    )


@router.delete("/{source}")
async def delete_document_endpoint(source: str):
    delete_from_index(source, True)
    delete_from_blob(source)
    return JSONResponse(content={"deleted": source})


@router.delete("")
async def clear_knowledge_base():
    results = vector_store.get()
    sources = list(
        set(metadata.get("source", "unknown") for metadata in results["metadatas"])
    )

    for source in sources:
        delete_from_index(source, True)
        delete_from_blob(source)

    return JSONResponse(content={"deleted": sources})