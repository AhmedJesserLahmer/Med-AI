from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import chat_history_collection
from schemas import ChatRequest, ChatResponse
from rag_model import RAG_Solution

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
    answer = RAG_Solution(request.question)
    await chat_history_collection.insert_one({
        "user_message": request.question,
        "ai_response": answer
    })
    return {"response": answer}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
