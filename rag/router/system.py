from fastapi import APIRouter

router = APIRouter(tags=["System"])


@router.post("/health")
def health():
    return {"status": "ok"}
