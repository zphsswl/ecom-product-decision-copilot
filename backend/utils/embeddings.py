from os import getenv
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

# 显式加载 backend/.env
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

EMBEDDING_MODEL = getenv("EMBEDDING_MODEL", "gemini-embedding-001")
EMBEDDING_DIMENSION = int(getenv("EMBEDDING_DIMENSION", "1536"))


def get_embedding_api_key() -> str:
    api_key = getenv("EMBEDDING_API_KEY") or getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("EMBEDDING_API_KEY or GEMINI_API_KEY is missing in .env")
    return api_key


def get_embedding_client():
    return genai.Client(api_key=get_embedding_api_key())


def embed_document_text(text: str) -> list[float]:
    if not text or not text.strip():
        raise ValueError("Document text for embedding is empty")

    client = get_embedding_client()

    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text.strip(),
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT",
            output_dimensionality=EMBEDDING_DIMENSION,
        ),
    )

    return result.embeddings[0].values


def embed_query_text(text: str) -> list[float]:
    if not text or not text.strip():
        raise ValueError("Query text for embedding is empty")

    client = get_embedding_client()

    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text.strip(),
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=EMBEDDING_DIMENSION,
        ),
    )

    return result.embeddings[0].values


if __name__ == "__main__":
    print("EMBEDDING_API_KEY loaded:", bool(get_embedding_api_key()))