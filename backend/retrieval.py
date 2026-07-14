"""Hybrid retrieval: dense (Pinecone) + sparse (BM25) search, Reciprocal Rank
Fusion, and cross-encoder reranking -- ported from RAG_New_solution.ipynb so
the same pipeline that was NDCG-evaluated in the notebook is what actually
serves live queries.

The BM25 corpus and chunk_ids are rebuilt from ./data at import time (module
load, i.e. once per backend process start) rather than stored as a separate
artifact -- rebuilding is cheap (CSV parse + text split, no ML) and keeps a
single source of truth with backend/ingest.py's chunking.
"""
import os
import re
from typing import Dict, List

from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from pinecone import Pinecone
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder

from ingestion import EMBEDDING_MODEL_NAME, load_and_chunk

load_dotenv()

DATA_DIR = os.getenv("DATA_DIR", "./data")

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = "lab-rag-index"
PINECONE_NAMESPACE = "ns1"

RERANKER_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

# --- Load once at process start -------------------------------------------

embedding_model = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL_NAME,
    encode_kwargs={"normalize_embeddings": True},
)

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)

reranker = CrossEncoder(RERANKER_MODEL_NAME)

docs_processed = load_and_chunk(DATA_DIR)
chunk_ids: List[str] = [f"vec{i}" for i in range(len(docs_processed))]
id_to_text: Dict[str, str] = {cid: doc.page_content for cid, doc in zip(chunk_ids, docs_processed)}
id_to_metadata: Dict[str, dict] = {cid: doc.metadata for cid, doc in zip(chunk_ids, docs_processed)}


def tokenize(text: str) -> List[str]:
    return re.findall(r"\w+", text.lower())


bm25_corpus_tokens = [tokenize(doc.page_content) for doc in docs_processed]
bm25 = BM25Okapi(bm25_corpus_tokens)


# --- Retrieval strategies ---------------------------------------------------


def dense_search(query: str, top_k: int = 10) -> List[dict]:
    query_vector = embedding_model.embed_query(query)
    results = index.query(
        namespace=PINECONE_NAMESPACE,
        vector=query_vector,
        top_k=top_k,
        include_metadata=True,
    )
    return [
        {"id": match["id"], "score": float(match["score"]), "text": match["metadata"]["text"]}
        for match in results["matches"]
    ]


def sparse_search(query: str, top_k: int = 10) -> List[dict]:
    scores = bm25.get_scores(tokenize(query))
    ranked_idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
    return [
        {"id": chunk_ids[i], "score": float(scores[i]), "text": id_to_text[chunk_ids[i]]}
        for i in ranked_idx
    ]


def reciprocal_rank_fusion(rankings: List[List[str]], k: int = 60) -> List[str]:
    fused_scores: Dict[str, float] = {}
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking):
            fused_scores[doc_id] = fused_scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
    return sorted(fused_scores, key=fused_scores.get, reverse=True)


def hybrid_search_fused(query: str, top_k: int = 10, candidate_pool: int = 30) -> List[dict]:
    dense_ids = [r["id"] for r in dense_search(query, candidate_pool)]
    sparse_ids = [r["id"] for r in sparse_search(query, candidate_pool)]
    fused_ids = reciprocal_rank_fusion([dense_ids, sparse_ids])[:top_k]
    return [{"id": doc_id, "text": id_to_text[doc_id]} for doc_id in fused_ids if doc_id in id_to_text]


def rerank(query: str, candidates: List[dict], top_k: int = 5) -> List[dict]:
    if not candidates:
        return []
    pairs = [(query, candidate["text"]) for candidate in candidates]
    scores = reranker.predict(pairs)
    for candidate, score in zip(candidates, scores):
        candidate["rerank_score"] = float(score)
    return sorted(candidates, key=lambda c: c["rerank_score"], reverse=True)[:top_k]


def hybrid_search(query: str, top_k: int = 5, candidate_pool: int = 30) -> List[dict]:
    fused = hybrid_search_fused(query, top_k=candidate_pool, candidate_pool=candidate_pool)
    return rerank(query, fused, top_k=top_k)
