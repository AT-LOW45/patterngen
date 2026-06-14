
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
        for chunk in header_chunks:
            chunk.metadata.update(doc.metadata)
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


async def search_index(query: str, k: int = 3) -> str:
    results = await vector_store.asimilarity_search(query, k=k)
    return "\n\n".join([doc.page_content for doc in results])


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
