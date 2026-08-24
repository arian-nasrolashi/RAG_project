from fastapi import FastAPI
from pydantic import BaseModel
from retrieval import search, create_context
import requests

app = FastAPI()


# ==========================================
# Linux API
# ==========================================

LINUX_API_URL = "http://172.20.6.181:8000/search"


# ==========================================
# Request Model
# ==========================================

class Question(BaseModel):
    question: str


# ==========================================
# Home
# ==========================================

@app.get("/")
def home():
    return {
        "message": "Windows Retrieval API is working"
    }


# ==========================================
# Search
# ==========================================

@app.post("/search")
def search_api(data: Question):

    results = search(data.question)

    return {
        "question": data.question,
        "results": results
    }


# ==========================================
# Ask
# ==========================================

@app.post("/ask")
def ask(data: Question):

    # 1. Search in FAISS
    results = search(data.question)

    # No relevant information
    if not results:
        return {
            "question": data.question,
            "answer": "متأسفم، اطلاعات مرتبطی پیدا نشد."
        }

    # 2. Create context
    context = create_context(results)

    # 3. Combine context + question
    prompt = f"""
بر اساس اطلاعات زیر به سؤال کاربر پاسخ بده.

فقط از اطلاعات موجود در Context استفاده کن.
اگر پاسخ در Context وجود ندارد، بگو اطلاعات کافی برای پاسخ وجود ندارد.

Context:
--------------------
{context}
--------------------

Question:
{data.question}
"""

    # 4. Send one request to Linux
    response = requests.post(
        LINUX_API_URL,
        json={
            "question": prompt
        },
        timeout=120
    )

    response.raise_for_status()

    # 5. Get Linux response
    result = response.json()

    # 6. Return final answer
    return {
        "question": data.question,
        "answer": result["results"]
    }


# ==========================================
# Run
# ==========================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000
    )
