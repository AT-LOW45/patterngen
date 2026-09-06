from typing import Literal
from pydantic import BaseModel, Field

Severity = Literal["warning", "error"]


class ReviewResultSchema(BaseModel):
    severity: Severity = Field(
        description="'error' for issues that undermine the ADR or would mislead code generation; 'warning' for advisory concerns."
    )
    section: str = Field(
        description="The ADR section the finding relates to (e.g. 'Decision'), or 'document' for whole-document issues."
    )
    message: str = Field(description="One concise, actionable sentence describing the issue.")


class ReviewOutputSchema(BaseModel):
    """Container so the LLM can return a list via with_structured_output."""

    findings: list[ReviewResultSchema] = Field(
        description="All issues found. Empty list if the ADR is sound."
    )


class ReviewResponseSchema(BaseModel):
    """API response: the findings plus whether the semantic (LLM) pass actually ran.

    Separate from ReviewOutputSchema (which the LLM fills) so `llm_ok` isn't something
    the model is asked to produce."""

    findings: list[ReviewResultSchema]
    llm_ok: bool = Field(
        default=True,
        description="False when the semantic (LLM) pass errored — findings are structural-only.",
    )
