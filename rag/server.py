from db.chroma_helper import delete_source
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from schema.boilerplate_schema import GenerateBoilerplateRequest
from service.boilerplate_service import run_generate_boilerplate
from fastapi import UploadFile, File
from db.chroma_helper import vector_store
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


@app.post("/generate-boilerplate")
async def generate_boilerplate(request: GenerateBoilerplateRequest):
    result = await run_generate_boilerplate(request)
    return JSONResponse(content={"code": result})


@app.post("/index-document")
async def index_document_endpoint(file: UploadFile = File(...), source: str = ""):
    content = await file.read()
    text = content.decode("utf-8")
    source_name = source or file.filename or "unknown"
    
    result = await kb_index_document(text, source_name)
    return JSONResponse(content={"result": result})


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
async def delete_document(source: str):
    delete_source(source, True)


@app.delete("/knowledge-base")
async def clear_knowledge_base():
    results = vector_store.get()
    sources = list(
        set(metadata.get("source", "unknown") for metadata in results["metadatas"])
    )

    for source in sources:
        delete_source(source, True)

    return JSONResponse(content={"deleted": sources})
