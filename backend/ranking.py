"""Pure ranking math shared by retrieval.py and eval.py -- no Pinecone, no
embedding/reranker models, no network calls. Kept separate so both can be
unit-tested without needing PINECONE_API_KEY or downloading any ML models.
"""
import math
from typing import Dict, List


def ndcg_at_k(relevances: List[int], k: int) -> float:
    relevances = relevances[:k]
    dcg = sum((2 ** rel - 1) / math.log2(i + 2) for i, rel in enumerate(relevances))
    ideal = sorted(relevances, reverse=True)
    idcg = sum((2 ** rel - 1) / math.log2(i + 2) for i, rel in enumerate(ideal))
    return dcg / idcg if idcg > 0 else 0.0


def reciprocal_rank_fusion(rankings: List[List[str]], k: int = 60) -> List[str]:
    fused_scores: Dict[str, float] = {}
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking):
            fused_scores[doc_id] = fused_scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
    return sorted(fused_scores, key=fused_scores.get, reverse=True)
