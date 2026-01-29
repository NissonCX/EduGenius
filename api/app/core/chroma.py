"""
ChromaDB integration for vector storage and retrieval.
Each document gets its own collection named by MD5 hash.
"""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional, Any
import hashlib

# ChromaDB client configuration
chroma_client = chromadb.PersistentClient(
    path="./chroma_db",
    settings=Settings(
        anonymized_telemetry=False,
        allow_reset=True
    )
)


def get_collection_name(md5_hash: str) -> str:
    """
    Generate ChromaDB collection name from MD5 hash.

    Args:
        md5_hash: 32-character MD5 hash

    Returns:
        Collection name in format 'doc_{md5_hash}'
    """
    return f"doc_{md5_hash}"


def create_document_collection(md5_hash: str) -> str:
    """
    Create a new ChromaDB collection for a document.

    Args:
        md5_hash: Document MD5 hash

    Returns:
        Name of the created collection
    """
    collection_name = get_collection_name(md5_hash)

    # Check if collection already exists (ChromaDB v0.6.0+)
    try:
        # 尝试获取集合，如果存在则直接返回
        chroma_client.get_collection(collection_name)
        return collection_name
    except Exception:
        # 集合不存在，创建新集合
        chroma_client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  # Using cosine similarity
        )
        return collection_name


def get_document_collection(md5_hash: str):
    """
    Get existing ChromaDB collection for a document.

    Args:
        md5_hash: Document MD5 hash

    Returns:
        ChromaDB collection object or None if not exists
    """
    collection_name = get_collection_name(md5_hash)

    try:
        return chroma_client.get_collection(collection_name)
    except Exception:
        return None


def add_document_chunks(
    md5_hash: str,
    chunks: List[str],
    embeddings: List[List[float]],
    metadata: Optional[List[Dict[str, Any]]] = None
) -> None:
    """
    Add document chunks to ChromaDB collection.

    Args:
        md5_hash: Document MD5 hash
        chunks: List of text chunks
        embeddings: List of embedding vectors for each chunk
        metadata: Optional metadata for each chunk (chapter, page, etc.)
    """
    collection = get_document_collection(md5_hash)
    if not collection:
        collection_name = create_document_collection(md5_hash)
        collection = chroma_client.get_collection(collection_name)

    # Generate IDs for chunks
    ids = [f"{md5_hash}_{i}" for i in range(len(chunks))]

    # Prepare metadata if not provided
    if metadata is None:
        metadata = [{"index": i} for i in range(len(chunks))]

    # Add chunks to collection
    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadata
    )


def query_document_chunks(
    md5_hash: str,
    query_embedding: List[float],
    n_results: int = 5,
    where: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Query document chunks by similarity.

    Args:
        md5_hash: Document MD5 hash
        query_embedding: Query embedding vector
        n_results: Number of results to return
        where: Optional metadata filter

    Returns:
        Query results with documents, metadata, and distances
    """
    collection = get_document_collection(md5_hash)
    if not collection:
        return {"documents": [], "metadatas": [], "distances": []}

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where
    )

    return results


def search_documents(
    query_text: str,
    md5_hash: str,
    embedding_model,  # DashScope embedding function
    n_results: int = 5
) -> List[Dict[str, Any]]:
    """
    搜索文档相关内容（RAG 检索）

    Args:
        query_text: 查询文本
        md5_hash: 文档 MD5
        embedding_model: 嵌入模型函数
        n_results: 返回结果数量

    Returns:
        相关文档片段列表
    """
    from dashscope import TextEmbedding

    # 生成查询向量
    response = TextEmbedding.call(
        model='text-embedding-v2',
        input=query_text,
        text_type='query'
    )

    if response.status_code != 200:
        raise Exception(f"Embedding 查询失败: {response.message}")

    query_embedding = response.output['embeddings'][0]['embedding']

    # 检索相关文档
    results = query_document_chunks(
        md5_hash=md5_hash,
        query_embedding=query_embedding,
        n_results=n_results
    )

    # 格式化结果
    retrieved_docs = []
    if results['documents']:
        for i, doc in enumerate(results['documents'][0]):
            retrieved_docs.append({
                'content': doc,
                'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                'distance': results['distances'][0][i] if results['distances'] else 0
            })

    return retrieved_docs


def delete_document_collection(md5_hash: str) -> bool:
    """
    Delete ChromaDB collection for a document.

    Args:
        md5_hash: Document MD5 hash

    Returns:
        True if deleted, False if didn't exist
    """
    collection_name = get_collection_name(md5_hash)

    try:
        chroma_client.delete_collection(collection_name)
        return True
    except Exception:
        return False


def get_collection_stats(md5_hash: str) -> Optional[Dict[str, Any]]:
    """
    Get statistics about a document's ChromaDB collection.

    Args:
        md5_hash: Document MD5 hash

    Returns:
        Dictionary with collection stats or None if not exists
    """
    collection = get_document_collection(md5_hash)
    if not collection:
        return None

    return {
        "name": collection.name,
        "count": collection.count(),
        "metadata": collection.metadata
    }
