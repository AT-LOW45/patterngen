import re
from typing import List
from config.llm_config import groq_llm
from schema.knowledgebase_schema import (
    ReviewResultSchema,
    ReviewOutputSchema,
    ReviewResponseSchema,
)
from langchain_core.prompts import ChatPromptTemplate


def missing_sections(
    content: str, required=["Status", "Scope", "Decision"]
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


def section_bodies(content: str) -> list[tuple[str, str]]:
    """(heading, body) for each H2 section in document order — the body is the text
    between a `## heading` and the next `## heading`."""
    sections: list[tuple[str, str]] = []
    # re.split with a capture group yields: [preamble, heading1, body1, heading2, body2, ...]
    parts = re.split(r"^##\s+(.+?)\s*$", content, flags=re.MULTILINE)
    for i in range(1, len(parts), 2):
        heading = parts[i].strip()
        body = parts[i + 1] if i + 1 < len(parts) else ""
        sections.append((heading, body))
    return sections


REVIEW_SYSTEM_PROMPT = """You are an ADR (Architecture Decision Record) reviewer. The ADR (markdown) will be \
used to ground LLM code generation, so flag anything that makes it useless or misleading for that.

Flag these:
- NON-SUBSTANTIVE content — a section whose text is gibberish (e.g. "rgrtg", "asdf"), filler, or otherwise \
fails to fulfil the section's purpose. Judge each section by what it is FOR:
  * Status: one of Proposed / Accepted / Deprecated / Superseded.
  * Scope: names a real system or component boundary.
  * Context: describes the actual situation or problem that motivated the decision.
  * Decision: states a concrete decision — what was chosen (ideally why).
  * Consequences: describes real outcomes or trade-offs.
  A section that doesn't do its job — e.g. a Decision of "decision" or "this is bad yo", a Context of "humus", \
a Scope of "rgrtg" — is NOT substantive; flag it with severity "warning".
- INTERNAL CONTRADICTIONS — one part conflicting with another. In particular, check that any code labelled \
CORRECT / recommended actually FOLLOWS the stated Decision (e.g. Decision says "never throw" but a recommended \
example throws). Severity "error".
- OFF-TOPIC text that has nothing to do with the decision being recorded. Severity "warning".
- BROKEN code snippets — syntactically invalid, or not matching the language or the decision they illustrate. \
Severity "error".

Calibration (avoid false positives):
- Terse is fine when it's genuine and specific — a Decision of "Use PostgreSQL for the primary datastore" is \
complete. Do NOT flag brevity or demand more detail when the meaning is clear.
- ADRs routinely include DELIBERATE anti-pattern examples labelled "INCORRECT", "don't do this", "bad", etc. — \
that is intentional teaching content; do NOT flag it.
- Do NOT flag missing sections, formatting, or length — those are checked separately.
- Only flag content that is genuinely gibberish, filler, contradictory, off-topic, or broken. If a section is \
real but imperfect, leave it.

For each problem, set an appropriate severity, name the section it belongs to (e.g. "Decision"), and give a \
short specific message. If the ADR is sound, return an empty findings list."""


async def run_llm_review(content: str) -> tuple[list[ReviewResultSchema], bool]:
    """Returns (findings, ok). `ok` is False when the LLM call errored, so the caller
    can tell 'review errored' apart from 'no issues found' — both otherwise look like []."""
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
        # Advisory feature — never fail the caller because the LLM hiccuped, but report
        # ok=False so a silent failure isn't mistaken for a clean review.
        print(f"LLM review failed: {error}")
        return [], False

    findings = response.findings if isinstance(response, ReviewOutputSchema) else []
    return findings, True


def run_deterministic_checks(content: str) -> list[ReviewResultSchema]:
    findings: list[ReviewResultSchema] = []

    for section in missing_sections(content):
        findings.append(
            ReviewResultSchema(
                severity="error", section=section, message=f"{section} is required"
            )
        )

    by_name = {heading.lower(): (heading, body) for heading, body in section_bodies(content)}

    # Required sections that exist but have no content (heading present, body blank).
    for required in ["Status", "Scope", "Decision"]:
        entry = by_name.get(required.lower())
        if entry and not entry[1].strip():
            findings.append(
                ReviewResultSchema(
                    severity="error", section=required, message=f"{required} has no content"
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
) -> ReviewResponseSchema:
    """
    orchestrator function to run ADR checks, run both deterministic and llm checks by default
    """
    results: list[ReviewResultSchema] = []
    llm_ok = True

    if "deterministic" in check_types:
        results = run_deterministic_checks(content)

    if "llm" in check_types:
        llm_findings, llm_ok = await run_llm_review(content)
        results = results + llm_findings

    return ReviewResponseSchema(findings=results, llm_ok=llm_ok)
