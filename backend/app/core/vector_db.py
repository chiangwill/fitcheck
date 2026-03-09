import chromadb

from app.config import settings

_client = None


async def get_client() -> chromadb.AsyncHttpClient:
    global _client
    if _client is None:
        _client = await chromadb.AsyncHttpClient(
            host=settings.chroma_host,
            port=settings.chroma_port,
        )
    return _client


async def get_collection(name: str):
    client = await get_client()
    return await client.get_or_create_collection(name)


async def upsert(collection_name: str, doc_id: str, embedding: list[float], metadata: dict):
    collection = await get_collection(collection_name)
    await collection.upsert(
        ids=[doc_id],
        embeddings=[embedding],
        metadatas=[metadata],
    )


async def delete(collection_name: str, doc_id: str):
    collection = await get_collection(collection_name)
    await collection.delete(ids=[doc_id])


async def query(collection_name: str, embedding: list[float], n_results: int = 5):
    collection = await get_collection(collection_name)
    return await collection.query(
        query_embeddings=[embedding],
        n_results=n_results,
    )
