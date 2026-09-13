from schema.knowledgebase_schema import SectionSpec

# The default ADR format. When per-KB ADR-format config lands, this becomes the fallback
# and review_adr accepts a caller-supplied catalog in its place — the review checks consume
# whatever catalog they're handed, so they don't change.
DEFAULT_SECTIONS: list[SectionSpec] = [
    {"title": "Status", "required": True, "purpose": "one of Proposed / Accepted / Deprecated / Superseded."},
    {"title": "Scope", "required": True, "purpose": "names a real system or component boundary."},
    {"title": "Context", "required": False, "purpose": "describes the actual situation or problem that motivated the decision."},
    {"title": "Decision", "required": True, "purpose": "states a concrete decision — what was chosen (ideally why)."},
    {"title": "Consequences", "required": False, "purpose": "describes real outcomes or trade-offs."},
]

# An ADR longer than this (whitespace-separated words) earns an advisory "consider trimming".
MAX_WORDS = 1500
