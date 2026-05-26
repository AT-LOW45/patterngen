from config.llm_config import groq_llm
from schema.boilerplate_schema import GenerateBoilerplateRequest
from langchain_core.prompts import ChatPromptTemplate


async def run_generate_boilerplate(request: GenerateBoilerplateRequest):
    context = "no context now, just do as you see fit"

    template = ChatPromptTemplate.from_messages(
        [
            ("system", f"Use these coding standards:\n\n{context}"),
            ("human", "{prompt}"),
        ]
    )
    chain = template | groq_llm
    response = await chain.ainvoke({"context": "", "prompt": request.query})
    return response.content
