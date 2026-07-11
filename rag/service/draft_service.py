# service/draft_service.py
import json

from storage.blob_storage import (
    save_draft_to_blob,
    get_draft_from_blob,
    delete_draft_from_blob,
    list_drafts_from_blob,
)


def list_drafts() -> list[dict]:
    """All drafts as `{ id, draft }` records (draft = the stored form object)."""
    return [{"id": draft_id, "draft": json.loads(body)} for draft_id, body in list_drafts_from_blob()]


def save_draft(draft_id: str, draft: dict) -> None:
    """Create or overwrite a draft (serialized to JSON for storage)."""
    save_draft_to_blob(draft_id, json.dumps(draft))


def get_draft(draft_id: str) -> dict | None:
    """The draft's form object, or None if it doesn't exist."""
    raw = get_draft_from_blob(draft_id)
    return json.loads(raw) if raw is not None else None


def delete_draft(draft_id: str) -> None:
    delete_draft_from_blob(draft_id)
