import os
from groq import Groq
from pinecone import Pinecone
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from dotenv import load_dotenv

load_dotenv()

# -------------------------
# Initialize Pinecone
# -------------------------
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

embedding_model = HuggingFaceEmbeddings(model_name="thenlper/gte-small")

index = pc.Index("lab-rag-index")

vectorstore = PineconeVectorStore(
    index=index,
    embedding=embedding_model,
    text_key="text",
    namespace="ns1"
)

# -------------------------
# Initialize Groq
# -------------------------
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# -------------------------
# RAG Pipeline
# -------------------------
def RAG_Solution(query: str):
    # 1️⃣ Retrieve
    docs = vectorstore.similarity_search(query, k=3)
    context = "\n".join([doc.page_content for doc in docs])

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

    return response.choices[0].message.content.strip()
