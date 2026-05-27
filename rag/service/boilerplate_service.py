from config.llm_config import groq_llm
from schema.boilerplate_schema import GenerateBoilerplateRequest
from langchain_core.prompts import ChatPromptTemplate

MOCK_CONTEXT = """
Company Coding Standards:

1. All functions must have type hints
2. Use async/await for all I/O operations
3. Error handling must use custom exception classes, not generic Exception
4. All API responses must follow the format: {"data": ..., "error": null} or {"data": null, "error": "message"}
5. Variable names must be snake_case
6. No print statements, use logging module instead
"""


def strip_code_fences(text: str) -> str:
    lines = text.strip().splitlines()
    if lines[0].startswith("```"):
        lines = lines[1:]
    if lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines)


async def run_generate_boilerplate(request: GenerateBoilerplateRequest) -> str:
    template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a code generator for {language}. Generate code that strictly follows these company coding standards:\n\n{context}\n\nReturn only the code, no explanations, no markdown code fences.",
            ),
            ("human", "{prompt}"),
        ]
    )

    chain = template | groq_llm
    response = await chain.ainvoke(
        {"context": MOCK_CONTEXT, "prompt": request.query, "language": request.language}
    )
    return strip_code_fences(str(response.content))
