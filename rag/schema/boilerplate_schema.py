from pydantic import BaseModel


class GenerateBoilerplateRequest(BaseModel):
    query: str
    language: str
    selection_context: str


class IndexDocumentRequest(BaseModel):
    content: str
    source: str
