from db.chroma_helper import add_documents
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from schema.boilerplate_schema import GenerateBoilerplateRequest
from service.boilerplate_service import run_generate_boilerplate
from langchain_core.documents import Document
from fastapi import UploadFile, File

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
