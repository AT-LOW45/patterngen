from pydantic import BaseModel


class GenerateBoilerplateRequest(BaseModel):
    query: str
    language: str
    selection_context: str
