from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from service.draft_service import list_drafts, save_draft, get_draft, delete_draft

# In-progress ADRs. Same domain as the knowledge base, but a distinct concern:
# opaque form JSON keyed by id, never indexed, one overwritable version per draft.
router = APIRouter(prefix="/knowledge-base/drafts", tags=["Drafts"])


@router.get("")
async def list_drafts_endpoint():
    """All drafts, for listing alongside published ADRs."""
    return JSONResponse(content={"drafts": list_drafts()})


@router.put("/{draft_id}")
async def save_draft_endpoint(draft_id: str, draft: dict):
    """Create or overwrite the draft `draft_id` (opaque form JSON, never indexed)."""
    save_draft(draft_id, draft)
    return JSONResponse(content={"id": draft_id, "saved": True})


@router.get("/{draft_id}")
async def get_draft_endpoint(draft_id: str):
    draft = get_draft(draft_id)
    if draft is None:
        raise HTTPException(status_code=404, detail=f"Draft '{draft_id}' not found")
    return JSONResponse(content={"id": draft_id, "draft": draft})


@router.delete("/{draft_id}")
async def delete_draft_endpoint(draft_id: str):
    delete_draft(draft_id)
    return JSONResponse(content={"deleted": draft_id})
