import re
from typing import List
from config.llm_config import groq_llm
from schema.knowledgebase_schema import ReviewResultSchema, ReviewOutputSchema
from langchain_core.prompts import ChatPromptTemplate


def missing_sections(
    content: str, required=["Status", "Context", "Decision"]
) -> List[str]:
    """
    Returns a list of required H2 section names that are missing from content.
    Empty list means all required sections are present.
    """
    # Find all H2 headings, e.g. "## Status" (allowing trailing whitespace, case-insensitive)
    found = {
        match.group(1).strip().lower()
        for match in re.finditer(r"^##\s+(.+?)\s*$", content, re.MULTILINE)
    }

    return [section for section in required if section.lower() not in found]


def unclosed_code_fence(content: str) -> bool:
    """
    Returns True if there's an unclosed code fence (odd number of ``` fence lines).
    """
    # Match lines that are code fence markers (``` or more backticks, optionally indented)
    fences = re.findall(r"^[ \t]*`{3,}", content, re.MULTILINE)
    return len(fences) % 2 == 1


MAX_WORDS = 1500


def word_count(content: str) -> int:
    """Number of whitespace-separated words in the document."""
    return len(content.split())


REVIEW_SYSTEM_PROMPT = """You are an ADR (Architecture Decision Record) reviewer. The ADR (markdown) \
will be used to ground LLM code generation, so flag only issues that would mislead that.

Flag ONLY:
- Internal contradictions — one part of the ADR conflicting with another. In particular, check that any \
code labelled CORRECT / recommended actually FOLLOWS the stated Decision (e.g. if the Decision says "never \
throw", a recommended example that throws is a contradiction).
- Off-topic or irrelevant text that has nothing to do with the decision being recorded.
- Code snippets that are syntactically broken, or that don't match the language or the decision they illustrate.

Important:
- ADRs routinely include DELIBERATE anti-pattern examples, labelled "INCORRECT", "don't do this", "bad", \
"never do this", etc. These are intentional teaching content — do NOT flag them as off-topic or as problems.
- Do NOT flag missing sections, formatting, or length — those are checked separately.
- Do NOT invent problems. If the ADR is sound, return an empty findings list."""


async def run_llm_review(content: str) -> list[ReviewResultSchema]:
    template = ChatPromptTemplate.from_messages(
        [
            ("system", REVIEW_SYSTEM_PROMPT),
            ("human", "Review this ADR:\n\n{content}"),
        ]
    )

    # with_structured_output forces the model to return a validated ReviewOutputSchema
    structured_llm = groq_llm.with_structured_output(ReviewOutputSchema)
    chain = template | structured_llm

    try:
        response = await chain.ainvoke({"content": content})
    except Exception as error:
        # Advisory feature — never fail the caller because the LLM hiccuped.
        print(f"LLM review failed: {error}")
        return []

    return response.findings if isinstance(response, ReviewOutputSchema) else []


def run_deterministic_checks(content: str) -> list[ReviewResultSchema]:
    findings: list[ReviewResultSchema] = []

    for section in missing_sections(content):
        findings.append(
            ReviewResultSchema(
                severity="error", section=section, message=f"{section} is required"
            )
        )

    if unclosed_code_fence(content):
        findings.append(
            ReviewResultSchema(
                severity="error",
                section="document",
                message="Unclosed code fence (```) — a code block isn't terminated",
            )
        )

    words = word_count(content)
    if words > MAX_WORDS:
        findings.append(
            ReviewResultSchema(
                severity="warning",
                section="document",
                message=f"ADR is long ({words} words, over {MAX_WORDS}) — consider trimming",
            )
        )

    return findings


async def review_adr(
    content: str, check_types: list[str] = ["deterministic", "llm"]
) -> ReviewOutputSchema:
    """
    orchestrator function to run ADR checks, run both deterministic and llm checks by default
    """
    results: list[ReviewResultSchema] = []

    if "deterministic" in check_types:
        results = run_deterministic_checks(content)

    if "llm" in check_types:
        llm_review_results = await run_llm_review(content)
        results = results + llm_review_results

    return ReviewOutputSchema(findings=results)
