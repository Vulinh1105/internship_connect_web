from __future__ import annotations

import os
from uuid import NAMESPACE_URL, uuid5

from dotenv import load_dotenv
from langchain_core.documents import Document
from app.modules.ai.providers.openai_client import create_embeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

load_dotenv()
COLLECTION_NAME = os.getenv(
    "QDRANT_COLLECTION",
    "internship-connect-openai")
EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")


# hàm tạo id ổn định cho từng chunk: kiểm tra chunk tồn tại
def _point_id(document: Document) -> str:
    chunk_id = document.metadata.get("chunk_id")
    document_id = document.metadata.get("document_id")
    chunk_index = document.metadata.get("chunk_index")
    identity = str(
        chunk_id
        or f"{document_id or ''}:{chunk_index or ''}:{document.page_content}"
    )
    return str(uuid5(NAMESPACE_URL, f"{COLLECTION_NAME}:{identity}"))

# chunk -> vectordb: lưu vào Qdrant
def create_vector_db(docs: list[Document]) -> QdrantVectorStore:
    embeddings = create_embeddings()
    client = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"))
    ids = [_point_id(doc) for doc in docs]

    if client.collection_exists(COLLECTION_NAME):
        store = QdrantVectorStore.from_existing_collection(
            embedding=embeddings,
            collection_name=COLLECTION_NAME,
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY"),
        )
        # kiểm tra chunk đã tồn tại
        existing = client.retrieve(
            COLLECTION_NAME,
            ids=ids,
            with_payload=False,
            with_vectors=False
        )
        existing_ids = {str(point.id) for point in existing}
        new_pairs = [(doc, point_id) for doc, point_id in zip(docs, ids) if point_id not in existing_ids]
        if new_pairs:
            batch_size = 10

            for start in range(0, len(new_pairs), batch_size):
                batch = new_pairs[start:start + batch_size]
                store.add_documents(
                    [doc for doc, _ in batch],
                    ids=[point_id for _, point_id in batch],
                )
        return store

    return QdrantVectorStore.from_documents(
        documents=docs,
        embedding=embeddings,
        ids=ids,
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY"),
        collection_name=COLLECTION_NAME,
        batch_size=5,
        prefer_grpc=False,
    )
