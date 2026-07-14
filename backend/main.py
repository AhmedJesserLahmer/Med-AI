from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import chat_history_collection
from schemas import ChatRequest, ChatResponse
from rag_model import RAG_Solution
import eval as ndcg_eval

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "message": "Med-AI backend is running.",
        "docs": "/docs",
        "rag_endpoint": {
            "path": "/rag",
            "method": "POST",
            "body": {"question": "What are the symptoms of diabetes?"}
        },
        "eval_endpoint": {
            "path": "/eval",
            "method": "GET",
            "description": "NDCG@k for dense/sparse/hybrid-fused/hybrid-reranked against a labeled query set"
        }
    }

@app.get("/rag")
def rag_help():
    return {
        "message": "Use POST /rag with JSON body.",
        "example": {"question": "What are the symptoms of diabetes?"}
    }

@app.post("/rag", response_model=ChatResponse)
async def chat(request: ChatRequest):
    answer, confidence, sources = RAG_Solution(request.question)
    await chat_history_collection.insert_one({
        "user_message": request.question,
        "ai_response": answer,
        "confidence": confidence,
        "sources": sources,
    })
    return {"response": answer, "confidence": confidence, "sources": sources}


@app.get("/eval")
def eval_retrieval():
    """Runs NDCG@k for dense-only/sparse-only/hybrid-fused/hybrid-reranked
    against a fixed, labeled query set (backend/eval.py) -- an on-demand
    accuracy check backed by ground truth, as opposed to the per-query
    confidence score returned by /rag which has no ground truth to compare
    against for arbitrary live questions.
    """
    return ndcg_eval.run_eval()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
