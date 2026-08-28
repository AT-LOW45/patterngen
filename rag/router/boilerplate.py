from fastapi import APIRouter
from fastapi.responses import JSONResponse
from schema.boilerplate_schema import GenerateBoilerplateRequest
from service.boilerplate_service import run_generate_boilerplate

router = APIRouter(prefix="/boilerplate", tags=["Boilerplate"])

@router.post("/generate-code", tags=["Boilerplate"])
async def generate_boilerplate(request: GenerateBoilerplateRequest):
    result = await run_generate_boilerplate(request)
    return JSONResponse(
        content={"edits": [{"search": e.search, "replace": e.replace} for e in result.edits]}
    )
