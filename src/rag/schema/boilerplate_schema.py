from pydantic import BaseModel

class GenerateBoilerplateRequest(BaseModel):
	query: str