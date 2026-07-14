"""One-off ingestion script: loads ./data, chunks it, embeds it, and upserts
every chunk into Pinecone with doc_id metadata (needed for the NDCG eval in
backend/eval.py to map retrieved chunks back to labeled relevance judgments).

Run manually whenever ./data changes:

    python backend/ingest.py

Not run automatically on every container start -- that would re-embed and
re-upsert on every deploy for no reason.
"""
import os

from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from pinecone import Pinecone
from tqdm import tqdm

from ingestion import EMBEDDING_MODEL_NAME, load_and_chunk

load_dotenv()

DATA_DIR = os.getenv("DATA_DIR", "./data")

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = "lab-rag-index"
PINECONE_NAMESPACE = "ns1"

UPSERT_BATCH_SIZE = 100


def batched(items, size):
    for i in range(0, len(items), size):
        yield items[i : i + size]


def main() -> None:
    docs_processed = load_and_chunk(DATA_DIR)
    print(f"Split into {len(docs_processed)} chunk(s) from {DATA_DIR}")

    chunk_ids = [f"vec{i}" for i in range(len(docs_processed))]

    embedding_model = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME,
        encode_kwargs={"normalize_embeddings": True},
    )

    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(PINECONE_INDEX_NAME)

    for batch in tqdm(list(batched(list(zip(chunk_ids, docs_processed)), UPSERT_BATCH_SIZE))):
        vectors = [
            {
                "id": chunk_id,
                "values": embedding_model.embed_query(doc.page_content),
                "metadata": {
                    "text": doc.page_content,
                    "source": doc.metadata.get("source", "unknown"),
                    "doc_id": doc.metadata.get("doc_id") or "",
                },
            }
            for chunk_id, doc in batch
        ]
        index.upsert(vectors=vectors, namespace=PINECONE_NAMESPACE)

    print("Ingestion complete.")


if __name__ == "__main__":
    main()
