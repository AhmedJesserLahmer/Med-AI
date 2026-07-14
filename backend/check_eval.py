"""CI regression check: runs the NDCG benchmark (backend/eval.py) and exits
non-zero if hybrid_reranked drops below NDCG_FLOOR. Retrieval-only -- needs
PINECONE_API_KEY (the same index backend/ingest.py populates) but not
GROQ_API_KEY or MONGODB_URI, since no LLM call or chat history is involved.
"""
import sys

import eval as ndcg_eval


def main() -> int:
    report = ndcg_eval.run_eval()
    floor = report["ndcg_floor"]
    scores = report["scores"]

    print(f"Evaluated {report['num_queries_evaluated']} labeled queries (k={report['k']})")
    for name, score in scores.items():
        status = "PASS" if score >= floor else "FAIL"
        print(f"  [{status}] {name:<16} NDCG@{report['k']} = {score:.3f}")

    if scores["hybrid_reranked"] < floor:
        print(f"\nNDCG regression: hybrid_reranked={scores['hybrid_reranked']:.3f} < floor {floor}")
        return 1

    print("\nAll NDCG checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
