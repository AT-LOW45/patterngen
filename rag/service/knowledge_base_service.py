# service/knowledge_base_service.py
from langchain_core.documents import Document
from langchain_core.indexing import IndexingResult
from db.chroma_helper import add_to_index
from storage.blob_storage import upload_to_blob

async def index_document(content: str, source: str) -> IndexingResult:
    # store original in blob storage
    upload_to_blob(content, source)

    # index chunks in vector store
    document = Document(page_content=content, metadata={"source": source})
    result = add_to_index([document], source)

    return result