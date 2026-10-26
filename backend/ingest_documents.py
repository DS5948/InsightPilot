
from io import BytesIO
from pathlib import Path
import hashlib

import chromadb
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer


# Project paths
BASE_DIR = Path(__file__).parent
DOCUMENTS_DIR = BASE_DIR / "documents"
CHROMA_DIR = BASE_DIR / "chroma_db"

# Local embedding model
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Chunk settings
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150

COLLECTION_NAME = "business_reports"


def split_into_chunks(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[str]:
    """Split text into overlapping character-based chunks."""

    text = text.strip()

    if not text:
        return []

    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError(
            "overlap must be >= 0 and smaller than chunk_size"
        )

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end == len(text):
            break

        start = end - overlap

    return chunks


def extract_text(filename: str, file_bytes: bytes) -> str:
    """Extract text from an uploaded TXT or PDF file."""

    extension = Path(filename).suffix.lower()

    if extension == ".txt":
        text = file_bytes.decode("utf-8-sig")

    elif extension == ".pdf":
        reader = PdfReader(BytesIO(file_bytes))

        if reader.is_encrypted:
            raise ValueError(
                f"PDF '{filename}' is encrypted and cannot be read."
            )

        text = "\n".join(
            page.extract_text() or ""
            for page in reader.pages
        )

    else:
        raise ValueError(
            "Unsupported file type. Upload a TXT or PDF file."
        )

    if not text.strip():
        raise ValueError(
            f"No extractable text found in '{filename}'. "
            "If this is a scanned PDF, OCR will be needed."
        )

    return text


def get_chroma_collection():
    """Get the persistent Chroma collection."""

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    return collection


def ingest_document(
    filename: str,
    file_bytes: bytes,
) -> dict:
    """
    Extract, chunk, embed, and store one TXT or PDF document.

    Re-uploading a document with the same filename replaces its
    previous chunks without deleting other indexed documents.
    """

    if not filename or not filename.strip():
        raise ValueError("Filename cannot be empty.")

    if not file_bytes:
        raise ValueError("The uploaded file is empty.")

    # Extract text and create chunks.
    text = extract_text(filename, file_bytes)
    chunks = split_into_chunks(text)

    if not chunks:
        raise ValueError("No non-empty text chunks were created.")

    # Load the embedding model only when ingestion is requested.
    embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    # Connect to the persistent vector database.
    collection = get_chroma_collection()

    # Replace only this source's existing chunks.
    collection.delete(where={"source": filename})

    # Create stable, unique IDs based on the filename and content.
    document_hash = hashlib.sha256(
        file_bytes
    ).hexdigest()[:16]

    safe_name = Path(filename).name

    ids = [
        f"{safe_name}_{document_hash}_{index}"
        for index in range(len(chunks))
    ]

    metadatas = [
        {
            "source": safe_name,
            "chunk_index": index,
            "document_hash": document_hash,
        }
        for index in range(len(chunks))
    ]

    # Generate local vector embeddings.
    embeddings = embedding_model.encode(
        chunks,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    # Store the document chunks and their metadata.
    collection.add(
        ids=ids,
        documents=chunks,
        metadatas=metadatas,
        embeddings=embeddings.tolist(),
    )

    return {
        "filename": safe_name,
        "chunks_stored": len(chunks),
        "characters_extracted": len(text),
    }


def main():
    """Index the sample TXT files in the documents folder."""

    if not DOCUMENTS_DIR.exists():
        raise FileNotFoundError(
            f"Documents folder not found: {DOCUMENTS_DIR}"
        )

    document_paths = sorted(DOCUMENTS_DIR.glob("*.txt"))

    if not document_paths:
        raise FileNotFoundError(
            f"No .txt files found in {DOCUMENTS_DIR}"
        )

    print("Indexing sample documents...")

    for document_path in document_paths:
        file_bytes = document_path.read_bytes()

        result = ingest_document(
            filename=document_path.name,
            file_bytes=file_bytes,
        )

        print(
            f"Indexed {result['filename']}: "
            f"{result['chunks_stored']} chunks"
        )

    print("\nDocument ingestion complete.")
    print(f"Chroma database location: {CHROMA_DIR}")


if __name__ == "__main__":
    main()
