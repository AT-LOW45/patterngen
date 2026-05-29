from db.chroma_helper import add_documents, delete_source
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from schema.boilerplate_schema import GenerateBoilerplateRequest
from service.boilerplate_service import run_generate_boilerplate
from langchain_core.documents import Document
from fastapi import UploadFile, File
from db.chroma_helper import vector_store

app = FastAPI()


@app.post("/generate-boilerplate")
async def generate_boilerplate(request: GenerateBoilerplateRequest):
    result = await run_generate_boilerplate(request)
    return JSONResponse(content={"code": result})


@app.post("/index-document")
async def index_document(file: UploadFile = File(...), source: str = ""):
    content = await file.read()
    text = content.decode("utf-8")

    source_name = source or file.filename or "unknown"

    document = Document(page_content=text, metadata={"source": source_name})
    result = add_documents([document], source_name)

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
    delete_source(source)
