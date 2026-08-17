from fastapi import FastAPI
from pydantic import BaseModel
import requests

app = FastAPI()


class LLMRequest(BaseModel):
    question: str
    context: str


@app.get("/")
def home():
    return {"message": "LLM API is working"}


@app.post("/generate")
def generate(data: LLMRequest):

    prompt = f"""
بر اساس اطلاعات زیر به سؤال کاربر پاسخ بده.
فقط از اطلاعات موجود در Context استفاده کن.

Context:
{data.context}

Question:
{data.question}
"""

    response = requests.post(
        "http://127.0.0.1:11434/api/generate",
        json={
            "model": "qwen2.5:3b",
            "prompt": prompt,
            "stream": False
        },
        timeout=120
    )

    response.raise_for_status()

    result = response.json()

    return {
        "answer": result["response"]
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000
    )
