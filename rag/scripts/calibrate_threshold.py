"""
Calibrate the retrieval score_threshold used in db/chroma_helper.search_index.

Run it whenever you change the embedding model or add a batch of ADRs, because the
"right" threshold depends on how the current model scores your current content.

How it works: it scores a set of GENUINE queries (things you'd really ask) and a set
of JUNK queries (off-topic nonsense). The threshold should sit in the gap between the
lowest genuine score and the highest junk score. A wide gap = robust; no gap = the
model can't tell relevant from irrelevant and no threshold will fix it.

Usage (must run from the rag/ directory so imports resolve):
    cd rag
    uv run python scripts/calibrate_threshold.py

Edit the GENUINE and JUNK lists below to match your own knowledge base.
"""

import asyncio
import sys
from pathlib import Path

# allow running as `python scripts/calibrate_threshold.py` from the rag/ dir
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.chroma_helper import vector_store, search_index  # noqa: E402

# --- edit these to reflect your own ADRs ------------------------------------
GENUINE = [
    "create a hook to fetch a list of products for a customer",
    "how should I handle errors in an API route",
    "write a function to update a user record in the database",
    "add a mutation to create a new order",
    "build a component that displays customer invoices",
]

JUNK = [
    "best recipe for chocolate chip cookies",
    "what is the weather like in Tokyo",
    "explain the history of the Roman empire",
    "how do I change a car tire",
    "write a poem about the ocean",
]
# ----------------------------------------------------------------------------


async def top_score(query: str) -> float:
    """Best relevance score across all chunks for a query (the deciding score)."""
    results = await vector_store.asimilarity_search_with_relevance_scores(query, k=50)
    return max((score for _, score in results), default=float("-inf"))


async def main() -> None:
    genuine_scores = [(q, await top_score(q)) for q in GENUINE]
    junk_scores = [(q, await top_score(q)) for q in JUNK]

    print("\nGENUINE queries (should be retrieved):")
    for q, s in genuine_scores:
        print(f"  {s:6.3f}  {q}")
    print("\nJUNK queries (should return nothing):")
    for q, s in junk_scores:
        print(f"  {s:6.3f}  {q}")

    floor = min(s for _, s in genuine_scores)   # lowest genuine
    ceiling = max(s for _, s in junk_scores)     # highest junk
    gap = floor - ceiling

    print("\n" + "-" * 50)
    print(f"genuine floor : {floor:.3f}")
    print(f"junk ceiling  : {ceiling:.3f}")
    print(f"gap           : {gap:.3f}")
    if gap > 0:
        suggested = round((floor + ceiling) / 2, 3)
        print(f"\n==> suggested score_threshold: {suggested}")
        print("    (midpoint of the gap; wider gap = more robust)")
    else:
        print("\n==> NO GAP: genuine and junk overlap. No single threshold separates")
        print("    them — the embedding model can't discriminate these queries.")


if __name__ == "__main__":
    asyncio.run(main())
