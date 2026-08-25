from fastapi import APIRouter
from fastapi.responses import JSONResponse
from schema.boilerplate_schema import GenerateBoilerplateRequest
from service.boilerplate_service import run_generate_boilerplate

router = APIRouter(prefix="/boilerplate", tags=["Boilerplate"])

@router.post("/generate-boilerplate", tags=["Boilerplate"])
async def generate_boilerplate(request: GenerateBoilerplateRequest):
    edit = await run_generate_boilerplate(request)
    return JSONResponse(content={"search": edit.search, "replace": edit.replace})
