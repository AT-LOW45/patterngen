from db.chroma_helper import delete_from_index
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from schema.boilerplate_schema import GenerateBoilerplateRequest
from service.boilerplate_service import run_generate_boilerplate
from fastapi import UploadFile, File
from db.chroma_helper import vector_store
from storage.blob_storage import delete_from_blob, get_from_blob
from service.knowledge_base_service import index_document as kb_index_document

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/generate-boilerplate", tags=["Boilerplate"])
async def generate_boilerplate(request: GenerateBoilerplateRequest):
    result = await run_generate_boilerplate(request)
    return JSONResponse(content={"code": result})


@app.post("/index-document", tags=["Knowledge Base"])
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


@app.get("/knowledge-base/{source}/raw")
async def get_document_raw(source: str):
    content = get_from_blob(source)
    return JSONResponse(content={"source": source, "content": content})


@app.get("/knowledge-base")
async def get_knowledge_base():
    results = vector_store.get()

    # extract unique sources from metadata
    sources = list(
        set(metadata.get("source", "unknown") for metadata in results["metadatas"])
    )

    return JSONResponse(content={"sources": sources})


@app.get("/knowledge-base/{source}")
async def get_document_content(source: str):
    results = vector_store.get(where={"source": source})

    chunks = results["documents"]

    return JSONResponse(
        content={"source": source, "chunks": chunks, "chunk_count": len(chunks)}
    )


@app.delete("/knowledge-base/{source}")
async def delete_document_endpoint(source: str):
    delete_from_index(source, True)
    delete_from_blob(source)
    return JSONResponse(content={"deleted": source})


@app.delete("/knowledge-base")
async def clear_knowledge_base():
    results = vector_store.get()
    sources = list(
        set(metadata.get("source", "unknown") for metadata in results["metadatas"])
    )

    for source in sources:
        delete_from_index(source, True)
        delete_from_blob(source)

    return JSONResponse(content={"deleted": sources})
