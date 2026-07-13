# 🩺 Med-AI

**A hybrid-retrieval medical AI assistant** — ask a health question, get an answer grounded in real medical text via dense + sparse retrieval, rank fusion, and cross-encoder reranking before it ever reaches the LLM.

![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=next.js&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-47A248?style=for-the-badge&logo=mongodb&logoColor=white)
![Pinecone](https://img.shields.io/badge/Pinecone-1C17FF?style=for-the-badge&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-F55036?style=for-the-badge&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

---

## ✨ What makes the retrieval "hybrid"

| Stage | What it does |
|---|---|
| 🟠 **Dense search** | Pinecone + `thenlper/gte-small` embeddings — catches semantic similarity |
| 🟡 **Sparse search** | BM25 (`rank_bm25`) over the same chunks — catches exact keyword/acronym matches dense search misses |
| 🔴 **Rank fusion** | Reciprocal Rank Fusion (RRF) merges both ranked lists without needing comparable score scales |
| 🟤 **Reranking** | A cross-encoder (`ms-marco-MiniLM-L-6-v2`) rescopes the fused candidates for the final, sharpest ordering |
| 🟢 **Evaluation** | NDCG@k compares dense-only vs. sparse-only vs. fused vs. reranked, so the pipeline's gains are measurable, not just assumed |

All of this — ingestion (PDF/DOCX/HTML/CSV/TXT), hybrid retrieval, fusion, reranking, and NDCG evaluation — lives in [`RAG_New_solution.ipynb`](./RAG_New_solution.ipynb). The FastAPI backend currently serves the simpler dense-only path in production (`backend/rag_model.py`); the notebook is where the hybrid pipeline is developed and evaluated.

---

## 🏗️ Architecture

<img src="./docs/architecture.svg" alt="Med-AI hybrid RAG architecture diagram" width="100%" />

---

## 🔁 Request sequence

One "ask a question" round trip, end to end:

<img src="./docs/sequence-diagram.svg" alt="Med-AI request sequence diagram" width="100%" />

---

## 🧱 Stack

- **Frontend:** Next.js (React) — chat UI, calls the backend directly
- **Backend:** FastAPI — `POST /rag`
- **Database:** MongoDB — chat history (`chat_history` collection)
- **Vector store:** Pinecone — dense embeddings (`gte-small`)
- **Sparse index:** BM25 (`rank_bm25`) — notebook only, for hybrid retrieval
- **LLM:** Groq (`llama-3.3-70b-versatile`)
- **Reranker:** `cross-encoder/ms-marco-MiniLM-L-6-v2` — notebook only

## 📂 Ingestion

`RAG_New_solution.ipynb` ingests a folder of mixed-format files (`.txt`, `.md`, `.pdf`, `.docx`, `.html`/`.htm`, `.csv`), chunks them, embeds them, and upserts them into Pinecone — plus builds the in-memory BM25 corpus used for hybrid search.

## 🚀 Running locally

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Environment variables (see `.env`):

- `PINECONE_API_KEY`, `PINECONE_ENV`
- `GROQ_API_KEY`, `GROQ_MODEL`
- `MONGODB_URI`, `MONGODB_DB_NAME`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_URL` (e.g. `http://localhost:8000/rag`) if the backend isn't proxied.

### With Docker

```bash
docker compose up --build
```

Brings up `mongo`, `backend` (FastAPI, port 8000) and `frontend` (Next.js, port 3000) together.
