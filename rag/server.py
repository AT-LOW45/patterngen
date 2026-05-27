from fastapi import FastAPI
from fastapi.responses import JSONResponse
from schema.boilerplate_schema import GenerateBoilerplateRequest
from service.boilerplate_service import run_generate_boilerplate

app = FastAPI()


@app.post("/generate-boilerplate")
async def generate_boilerplate(request: GenerateBoilerplateRequest):
    result = await run_generate_boilerplate(request)
    return JSONResponse(content={"code": result})
