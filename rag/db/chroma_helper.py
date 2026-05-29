from langchain_chroma.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
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

splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)


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
    vector_store.delete(where={"source": source})
