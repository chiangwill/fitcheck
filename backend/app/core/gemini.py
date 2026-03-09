from google import genai

from app.config import settings

client = genai.Client(api_key=settings.gemini_api_key)


async def generate(prompt: str) -> str:
    response = await client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return response.text


async def embed(text: str) -> list[float]:
    response = await client.aio.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
    )
    return response.embeddings[0].values
