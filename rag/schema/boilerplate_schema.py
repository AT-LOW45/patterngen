from pydantic import BaseModel, Field


class GenerateBoilerplateRequest(BaseModel):
    query: str
    language: str
    selection_context: str
    file_content: str = ""


class BoilerplateEdit(BaseModel):
    """A single search/replace edit the extension applies to the open file."""

    search: str = Field(
        description=(
            "The exact block of existing code to replace, copied verbatim from the "
            "file (same text and indentation). Empty string when there is no anchor, "
            "e.g. an empty file."
        )
    )
    replace: str = Field(
        description=(
            "The code to put in place of `search`, following the standards. No import "
            "statements, no markdown fences."
        )
    )


class IndexDocumentRequest(BaseModel):
    content: str
    source: str


class CreateDocumentRequest(BaseModel):
    content: str
