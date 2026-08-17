
from fastapi import FastAPI
from pydantic import BaseModel
from retrieval import search, create_context
import requests

app = FastAPI()


# ==========================================
# 1. Linux API
# ==========================================

LINUX_API_URL = "http://IP_LINUX:8000/generate"


# ==========================================
# 2. Request Model
# ==========================================

class Question(BaseModel):
    question: str


# ==========================================
# 3. Home
# ==========================================

@app.get("/")
def home():
    return {
        "message": "Windows Retrieval API is working"
    }


# ==========================================
# 4. Search
# ==========================================

@app.post("/search")
def search_api(data: Question):

    results = search(data.question)

    return {
        "question": data.question,
        "results": results
    }


# ==========================================
# 5. Ask
# ==========================================

@app.post("/ask")
def ask(data: Question):

    # جستجو در FAISS
    results = search(data.question)

    # اگر نتیجه‌ای پیدا نشد
    if not results:
        return {
            "question": data.question,
            "answer": "متأسفم، اطلاعات مرتبطی پیدا نشد."
        }

    # ساخت Context
    context = create_context(results)

    # ارسال سؤال + Context به Linux
    response = requests.post(
        LINUX_API_URL,
        json={
            "question": data.question,
            "context": context
        },
        timeout=120
    )

    response.raise_for_status()

    # دریافت پاسخ Linux
    result = response.json()

    # برگرداندن جواب به کاربر
    return {
        "question": data.question,
        "answer": result["answer"]
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000
    )
