import math
import os

from groq import Groq
from dotenv import load_dotenv

import retrieval

load_dotenv()

# -------------------------
# Initialize Groq
# -------------------------
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

TOP_K = 5


def _confidence_from_rerank_scores(candidates: list[dict]) -> float:
    """Cross-encoder rerank scores are unbounded logits, not probabilities --
    squash the top candidate's score into [0, 1] with a sigmoid so it reads as
    a confidence signal callers can log/threshold on.
    """
    if not candidates:
        return 0.0
    top_score = candidates[0].get("rerank_score", 0.0)
    return 1.0 / (1.0 + math.exp(-top_score))


def _sources_from_candidates(candidates: list[dict]) -> list[str]:
    sources = []
    for candidate in candidates:
        metadata = retrieval.id_to_metadata.get(candidate["id"], {})
        title = metadata.get("title") or metadata.get("source") or candidate["id"]
        if title not in sources:
            sources.append(title)
    return sources


# -------------------------
# RAG Pipeline
# -------------------------
def RAG_Solution(query: str) -> tuple[str, float, list[str]]:
    # 1️⃣ Retrieve (dense + sparse -> RRF fusion -> cross-encoder rerank)
    candidates = retrieval.hybrid_search(query, top_k=TOP_K)
    context = "\n".join(candidate["text"] for candidate in candidates)

    # 2️⃣ Prompt
    system_prompt = (
        "You are a helpful medical AI assistant. "
        "Answer using only the provided context. "
        "Always answer in the same language as the user's question."
    )

    user_prompt = f"""Context:
{context}

Question:
{query}
"""

    # 3️⃣ Generate
    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    )

    answer = response.choices[0].message.content.strip()
    confidence = _confidence_from_rerank_scores(candidates)
    sources = _sources_from_candidates(candidates)

    return answer, confidence, sources
