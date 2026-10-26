
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer
from functools import lru_cache


BASE_DIR = Path(__file__).parent
CHROMA_DIR = BASE_DIR / "chroma_db"

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
COLLECTION_NAME = "business_reports"
TOP_K = 5


@lru_cache(maxsize=1)
def get_embedding_model():
    return SentenceTransformer(EMBEDDING_MODEL_NAME)

def get_collection():
    """Connect to the persistent Chroma collection."""

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    return client.get_collection(name=COLLECTION_NAME)


def retrieve_documents(
    question: str,
    top_k: int = TOP_K,
) -> list[dict]:
    """Return relevant, non-duplicate document chunks."""

    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    collection = get_collection()
    available_chunks = collection.count()

    if available_chunks == 0:
        return []

    # Load the embedding model only when retrieval is requested.
    embedding_model = get_embedding_model()

    question_embedding = embedding_model.encode(
        question,
        normalize_embeddings=True,
    )

    results = collection.query(
        query_embeddings=[question_embedding.tolist()],
        n_results=min(top_k, available_chunks),
        include=["documents", "metadatas", "distances"],
    )

    retrieved = []
    seen_chunks = set()

    documents = results["documents"][0] or []
    metadatas = results["metadatas"][0] or []
    distances = results["distances"][0] or []

    for document, metadata, distance in zip(
        documents,
        metadatas,
        distances,
    ):
        if not document or not metadata:
            continue

        source = metadata.get("source", "unknown")
        chunk_index = metadata.get("chunk_index", -1)

        # Avoid returning the same source text twice.
        deduplication_key = (source, document.strip())

        if deduplication_key in seen_chunks:
            continue

        seen_chunks.add(deduplication_key)

        retrieved.append({
            "text": document,
            "source": source,
            "chunk_index": chunk_index,
            "distance": distance,
        })

    return retrieved


if __name__ == "__main__":
    question = input(
        "Ask a question about the business reports: "
    )

    try:
        results = retrieve_documents(question)

        if not results:
            print("No document chunks are available.")
        else:
            for index, result in enumerate(results, start=1):
                print(f"\n--- Result {index} ---")
                print(f"Source: {result['source']}")
                print(f"Chunk: {result['chunk_index']}")
                print(f"Distance: {result['distance']:.4f}")
                print(result["text"])

    except Exception as error:
        print(f"Error: {type(error).__name__}: {error}")
