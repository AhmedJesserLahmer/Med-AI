"""NDCG@k evaluation, ported from RAG_New_solution.ipynb, for the GET /eval
endpoint: an on-demand check of retrieval quality against a fixed set of
labeled queries. This is deliberately separate from the per-query confidence
score returned by /rag -- NDCG needs ground-truth relevant docs, which don't
exist for arbitrary live questions, so it can only ever be computed against a
known, labeled benchmark like TEST_QUERIES below.
"""
import math
from typing import Dict, List, Tuple

import retrieval

# Real test cases: each maps a natural question to the doc_id(s) in
# healthcare_rag_dataset.csv that should answer it. Documents of the same
# disease often repeat the same symptoms/treatments/risk_factors/prevention
# fields verbatim across their different document_types (Symptom Guide, FAQ,
# Prevention Guide, ...), so crediting every doc_id for that disease/field is
# correct, not lenient -- they're genuinely equally relevant.
#
# Beyond the original "what are the symptoms of X" queries (which are
# near-verbatim restatements of the indexed "Symptoms:" field and nearly
# solvable by keyword match alone), this set adds:
#   - paraphrased queries that never say the field name being asked about
#   - queries about treatments/prevention/risk factors, not just symptoms
#   - pairs of diseases with overlapping symptom vocabulary (e.g. influenza vs.
#     allergic rhinitis both cause a runny nose + fatigue) so dense/sparse/
#     rerank actually have to disambiguate instead of matching on a unique
#     disease-name keyword.
TEST_QUERIES: List[Tuple[str, List[str]]] = [
    # --- original symptom-guide queries (kept for continuity) ---
    ("What are the symptoms of conjunctivitis (pink eye)?", ["DOC-E6C0C42D", "DOC-EF53E84B"]),
    ("What are common symptoms of allergic rhinitis?", ["DOC-D8F798B2", "DOC-A921FFB8"]),
    ("What does eczema look like and what are its symptoms?", ["DOC-E911986D", "DOC-179D9829"]),
    ("What are the symptoms of hyperlipidemia?", ["DOC-1427E31F", "DOC-CEC0BC16"]),
    ("What are the symptoms of asthma?", ["DOC-2117F5AF", "DOC-5FF9D8C6"]),
    ("What are the symptoms of iron deficiency anemia?", ["DOC-6FF549B5", "DOC-74EC101D"]),
    ("What are the symptoms of type 2 diabetes?", ["DOC-1730475D", "DOC-ECFFDC24"]),
    ("What are the symptoms of a urinary tract infection?", ["DOC-64EEB1E0", "DOC-E2395F2A"]),
    # --- paraphrased, non-verbatim queries ---
    (
        "My eyes are red, itchy, and watery with some discharge -- what could be causing this?",
        ["DOC-E6C0C42D", "DOC-EF53E84B"],
    ),
    (
        "I can't stop sneezing, my nose is running, and my eyes are itchy -- could this be allergies?",
        ["DOC-D8F798B2", "DOC-A921FFB8"],
    ),
    (
        "I have a fever, chills, body aches, and a sore throat -- what's wrong with me?",
        ["DOC-3F30C4B8", "DOC-384A7224"],
    ),
    # --- treatment / prevention / risk-factor queries ---
    ("How is high cholesterol (hyperlipidemia) usually treated?", ["DOC-FEA8CCEE", "DOC-F731CE77"]),
    ("What can I do to keep my asthma from acting up?", ["DOC-33A23448", "DOC-42297E06"]),
    (
        "What increases someone's chances of getting coronary artery disease?",
        ["DOC-E2C5DDA9", "DOC-A1DAECC4"],
    ),
]

# NDCG@5 that hybrid_reranked should reliably clear on this labeled set --
# a lower floor than the easy baseline's ~0.93, since these queries are
# designed to actually stress retrieval instead of being solved by keyword
# match alone.
NDCG_FLOOR = 0.6

K = 5

RETRIEVAL_METHODS = {
    "dense_only": lambda q: [r["id"] for r in retrieval.dense_search(q, K)],
    "sparse_only": lambda q: [r["id"] for r in retrieval.sparse_search(q, K)],
    "hybrid_fused": lambda q: [r["id"] for r in retrieval.hybrid_search_fused(q, top_k=K)],
    "hybrid_reranked": lambda q: [r["id"] for r in retrieval.hybrid_search(q, top_k=K)],
}


def ndcg_at_k(relevances: List[int], k: int) -> float:
    relevances = relevances[:k]
    dcg = sum((2 ** rel - 1) / math.log2(i + 2) for i, rel in enumerate(relevances))
    ideal = sorted(relevances, reverse=True)
    idcg = sum((2 ** rel - 1) / math.log2(i + 2) for i, rel in enumerate(ideal))
    return dcg / idcg if idcg > 0 else 0.0


def chunk_ids_for_doc(doc_id: str) -> List[str]:
    """All chunk ids whose source metadata came from this doc_id (a document
    can span several chunks after splitting)."""
    return [
        chunk_id
        for chunk_id, metadata in retrieval.id_to_metadata.items()
        if metadata.get("doc_id") == doc_id
    ]


def _build_eval_set() -> List[dict]:
    eval_set = [
        {
            "query": query,
            "relevant_grades": {
                cid: 2
                for doc_id in doc_ids
                for cid in chunk_ids_for_doc(doc_id)
            },
        }
        for query, doc_ids in TEST_QUERIES
    ]
    return [example for example in eval_set if example["relevant_grades"]]


def evaluate_method(method_fn, eval_set: List[dict], k: int) -> float:
    scores = []
    for example in eval_set:
        ranked_ids = method_fn(example["query"])
        relevances = [example["relevant_grades"].get(doc_id, 0) for doc_id in ranked_ids]
        scores.append(ndcg_at_k(relevances, k))
    return sum(scores) / len(scores) if scores else 0.0


def run_eval() -> Dict[str, object]:
    eval_set = _build_eval_set()
    missing = len(TEST_QUERIES) - len(eval_set)

    scores = {
        name: evaluate_method(fn, eval_set, K)
        for name, fn in RETRIEVAL_METHODS.items()
    }

    return {
        "k": K,
        "ndcg_floor": NDCG_FLOOR,
        "num_queries_evaluated": len(eval_set),
        "num_queries_missing_docs": missing,
        "scores": scores,
    }
