import os

from langchain_chroma.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain_text_splitters import MarkdownTextSplitter
from langchain_core.documents import Document
from langchain_core.indexing import IndexingResult, index
from langchain_classic.indexes import SQLRecordManager

CHROMA_DB_PATH = "./chroma_db"
RECORD_MANAGER_DB = "sqlite:///./record_manager.db"
NAMESPACE = "chroma/patterngen"

embeddings = HuggingFaceEndpointEmbeddings(
    model="sentence-transformers/all-MiniLM-L6-v2",
    huggingfacehub_api_token=os.getenv("HUGGINGFACE_API_KEY"),
)

vector_store = Chroma(persist_directory=CHROMA_DB_PATH, embedding_function=embeddings)

record_manager = SQLRecordManager(namespace=NAMESPACE, db_url=RECORD_MANAGER_DB)
record_manager.create_schema()

splitter = MarkdownTextSplitter(chunk_size=1500, chunk_overlap=0, keep_separator=True)


def add_documents(documents: list[Document], source: str) -> IndexingResult:
    for doc in documents:
        doc.metadata["source"] = source

    chunks = splitter.split_documents(documents)

    result = index(
        chunks,
        record_manager,
        vector_store,
        cleanup="incremental",
        source_id_key="source",
    )
    return result


async def chroma_search(query: str, k: int = 3) -> str:
    results = await vector_store.asimilarity_search(query, k=k)
    return "\n\n".join([doc.page_content for doc in results])


def delete_source(source: str) -> None:
    # delete from vector store
    vector_store.delete(where={"source": source})

    # # delete from record manager
    # keys = record_manager.list_keys(group_ids=[source])
    # if keys:
    #     record_manager.delete_keys(keys)
