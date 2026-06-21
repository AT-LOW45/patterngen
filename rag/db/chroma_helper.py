
from langchain_chroma.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_core.documents import Document
from langchain_core.indexing import IndexingResult, index
from langchain_classic.indexes import SQLRecordManager

CHROMA_DB_PATH = "./chroma_db"
RECORD_MANAGER_DB = "sqlite:///./record_manager.db"
NAMESPACE = "chroma/patterngen"

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

vector_store = Chroma(persist_directory=CHROMA_DB_PATH, embedding_function=embeddings)

record_manager = SQLRecordManager(namespace=NAMESPACE, db_url=RECORD_MANAGER_DB)
record_manager.create_schema()

header_splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=[
        ("#", "title"),
        ("##", "section"),
        ("###", "subsection"),
    ],
    strip_headers=False,
)


def split_documents(documents: list[Document]) -> list[Document]:
    chunks = []
    for doc in documents:
        header_chunks = header_splitter.split_text(doc.page_content)
        for order, chunk in enumerate(header_chunks):
            chunk.metadata.update(doc.metadata)
            # preserve original document order so an ADR can be reassembled
            chunk.metadata["chunk_index"] = order
        chunks.extend(header_chunks)
    return chunks


def add_to_index(documents: list[Document], source: str) -> IndexingResult:
    for doc in documents:
        doc.metadata["source"] = source

    chunks = split_documents(documents)

    result = index(
        chunks,
        record_manager,
        vector_store,
        cleanup="incremental",
        source_id_key="source",
    )
    return result


def _assemble_source(source: str) -> str:
    """Fetch every chunk of one ADR and reassemble it in document order."""
    stored = vector_store.get(where={"source": source})
    pairs = list(zip(stored["metadatas"], stored["documents"]))
    pairs.sort(key=lambda p: p[0].get("chunk_index", 0))
    return "\n\n".join(doc for _, doc in pairs)


async def search_index(
    query: str,
    candidate_k: int = 36,
    score_threshold: float = 0.1,
    max_sources: int = 3,
) -> str:
    """
    Find which ADRs are relevant to the query, then return each relevant ADR in
    full (not just the matched chunks) so code examples are never dropped.

    - candidate_k: how many chunks to inspect when deciding which ADRs are relevant
    - score_threshold: an ADR's best-matching chunk must clear this to be included
    - max_sources: cap on how many ADRs to return, so a vague query can't pull in everything
    """
    scored = await vector_store.asimilarity_search_with_relevance_scores(
        query, k=candidate_k
    )

    # keep each source's best chunk score
    best_score: dict[str, float] = {}
    for doc, score in scored:
        source = doc.metadata.get("source")
        if source is None:
            continue
        if score > best_score.get(source, float("-inf")):
            best_score[source] = score

    # keep relevant sources, strongest first, capped
    relevant = sorted(
        (s for s, score in best_score.items() if score >= score_threshold),
        key=lambda s: best_score[s],
        reverse=True,
    )[:max_sources]

    if not relevant:
        return ""

    return "\n\n---\n\n".join(_assemble_source(source) for source in relevant)


def delete_from_index(source: str, clear_key: bool = False) -> None:
    """
    clears document from vector store while persisting the record. If clear_key is True, clears the record entirely
    """
    # delete from vector store
    vector_store.delete(where={"source": source})

    # # delete from record manager
    if clear_key:
        keys = record_manager.list_keys(group_ids=[source])
        if keys:
            record_manager.delete_keys(keys)
