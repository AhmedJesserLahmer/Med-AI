# Med-AI

Helpful medical AI assistant (RAG pipeline tuned to answer medical questions with more precision).

## Stack

- **Frontend:** Next.js (React)
- **Backend:** FastAPI
- **Database:** MongoDB (chat history)
- **Vector store:** Pinecone
- **LLM:** Groq API

## Running locally

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
