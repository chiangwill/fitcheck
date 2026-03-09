from app.core.gemini import embed
from app.core.vector_db import delete, upsert

RESUME_COLLECTION = "resumes"
JOB_COLLECTION = "jobs"


async def embed_and_store_resume(resume_id: int, text: str) -> str:
    embedding = await embed(text)
    doc_id = f"resume_{resume_id}"
    await upsert(
        collection_name=RESUME_COLLECTION,
        doc_id=doc_id,
        embedding=embedding,
        metadata={"resume_id": resume_id},
    )
    return doc_id


async def delete_resume_embedding(doc_id: str):
    await delete(RESUME_COLLECTION, doc_id)


async def embed_and_store_job(job_id: int, text: str) -> str:
    embedding = await embed(text)
    doc_id = f"job_{job_id}"
    await upsert(
        collection_name=JOB_COLLECTION,
        doc_id=doc_id,
        embedding=embedding,
        metadata={"job_id": job_id},
    )
    return doc_id
