import os
import json
import re
import logging

import faiss
import numpy as np
import pymupdf
import pytesseract

from PIL import Image
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

import requests


# =========================================================
# Logging
# =========================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =========================================================
# FastAPI
# =========================================================

app = FastAPI(
    title="RAG API",
    description="Windows RAG API with PDF upload and Linux LLM",
    version="1.0.0"
)


# =========================================================
# Configuration
# =========================================================

PDF_FOLDER = r"C:\Users\user\Documents\pdf.13"

VECTOR_FOLDER = "vector_store"

INDEX_FILE = os.path.join(
    VECTOR_FOLDER,
    "catalog.index"
)

METADATA_FILE = os.path.join(
    VECTOR_FOLDER,
    "metadata.json"
)

CHUNKS_FILE = "chunks.json"
EMBEDDINGS_FILE = "embeddings.json"

EMBEDDING_MODEL = "intfloat/multilingual-e5-small"

LINUX_API_URL = "http://172.20.6.181:8000/search"

MAX_RESULTS = 5

SCORE_THRESHOLD = 0.75


# =========================================================
# Load Embedding Model
# =========================================================

logger.info("Loading retrieval model...")

embedding_model = SentenceTransformer(
    EMBEDDING_MODEL
)

logger.info("Retrieval model loaded.")


# =========================================================
# Text Splitter
# =========================================================

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)


# =========================================================
# Retrieval Data
# =========================================================

index = None
metadata = []


# =========================================================
# Load Retrieval
# =========================================================

def load_retrieval():

    global index
    global metadata

    logger.info("Loading FAISS index...")

    if not os.path.exists(INDEX_FILE):

        raise FileNotFoundError(
            f"FAISS index not found: {INDEX_FILE}"
        )

    index = faiss.read_index(
        INDEX_FILE
    )

    logger.info(
        f"FAISS vectors: {index.ntotal}"
    )

    logger.info("Loading metadata...")

    if os.path.exists(METADATA_FILE):

        with open(
            METADATA_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            metadata = json.load(file)

    else:

        metadata = []

    logger.info(
        f"Metadata records: {len(metadata)}"
    )


# =========================================================
# Initial Retrieval Load
# =========================================================

load_retrieval()


# =========================================================
# Request Model
# =========================================================

class Question(BaseModel):

    question: str


# =========================================================
# JSON Helpers
# =========================================================

def load_json(
    path,
    default
):

    if not os.path.exists(path):

        return default

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


def save_json(
    path,
    data
):

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2
        )


# =========================================================
# Text Cleaning
# =========================================================

def clean_text(text):

    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    text = re.sub(
        r"\n\s*\n+",
        "\n\n",
        text
    )

    return text.strip()


# =========================================================
# OCR
# =========================================================

def extract_page_text(page):

    pix = page.get_pixmap(
        matrix=pymupdf.Matrix(
            2,
            2
        )
    )

    image = Image.frombytes(
        "RGB",
        [
            pix.width,
            pix.height
        ],
        pix.samples
    )

    return pytesseract.image_to_string(
        image,
        lang="fas+eng"
    )


# =========================================================
# Process Uploaded PDF
# =========================================================

def process_pdf(pdf_path):

    global index
    global metadata

    filename = os.path.basename(
        pdf_path
    )

    logger.info(
        f"Processing PDF: {filename}"
    )

    chunks = load_json(
        CHUNKS_FILE,
        []
    )

    embeddings = load_json(
        EMBEDDINGS_FILE,
        []
    )

    # -----------------------------------------------------
    # Prevent duplicate processing
    # -----------------------------------------------------

    for item in metadata:

        if item.get("source") == filename:

            raise ValueError(
                f"PDF '{filename}' already exists in RAG."
            )

    # -----------------------------------------------------
    # Generate next chunk ID
    # -----------------------------------------------------

    if chunks:

        next_chunk_id = max(
            item["chunk_id"]
            for item in chunks
        ) + 1

    else:

        next_chunk_id = 0

    new_chunks = []

    # -----------------------------------------------------
    # Open PDF
    # -----------------------------------------------------

    document = pymupdf.open(
        pdf_path
    )

    try:

        for page_number, page in enumerate(
            document,
            start=1
        ):

            text = extract_page_text(
                page
            )

            text = clean_text(
                text
            )

            if not text:

                continue

            page_chunks = splitter.split_text(
                text
            )

            for chunk in page_chunks:

                chunk = clean_text(
                    chunk
                )

                if len(chunk) < 50:

                    continue

                new_chunks.append({

                    "chunk_id": next_chunk_id,

                    "source": filename,

                    "page": page_number,

                    "text": chunk

                })

                next_chunk_id += 1

    finally:

        document.close()

    if not new_chunks:

        raise ValueError(
            "No usable text was extracted from the PDF."
        )

    logger.info(
        f"Created {len(new_chunks)} chunks."
    )

    # =====================================================
    # Embeddings
    # =====================================================

    texts = [

        "passage: " + item["text"]

        for item in new_chunks

    ]

    new_vectors = embedding_model.encode(

        texts,

        batch_size=8,

        normalize_embeddings=True,

        show_progress_bar=True

    )

    new_vectors = np.asarray(
        new_vectors,
        dtype="float32"
    )

    # =====================================================
    # FAISS
    # =====================================================

    if index is None:

        index = faiss.IndexFlatIP(
            new_vectors.shape[1]
        )

    if index.d != new_vectors.shape[1]:

        raise ValueError(
            "Embedding dimension does not match FAISS index."
        )

    index.add(
        new_vectors
    )

    faiss.write_index(
        index,
        INDEX_FILE
    )

    # =====================================================
    # Update Chunks
    # =====================================================

    chunks.extend(
        new_chunks
    )

    save_json(
        CHUNKS_FILE,
        chunks
    )

    # =====================================================
    # Update Embeddings
    # =====================================================

    for chunk, vector in zip(
        new_chunks,
        new_vectors
    ):

        embeddings.append({

            "chunk_id": chunk["chunk_id"],

            "source": chunk["source"],

            "page": chunk["page"],

            "text": chunk["text"],

            "embedding": vector.tolist()

        })

    save_json(
        EMBEDDINGS_FILE,
        embeddings
    )

    # =====================================================
    # Update Metadata
    # =====================================================

    metadata.extend(
        [
            {
                "chunk_id": item["chunk_id"],
                "source": item["source"],
                "page": item["page"],
                "text": item["text"]
            }

            for item in new_chunks
        ]
    )

    save_json(
        METADATA_FILE,
        metadata
    )

    # =====================================================
    # Result
    # =====================================================

    logger.info(
        f"PDF '{filename}' added successfully."
    )

    logger.info(
        f"Total FAISS vectors: {index.ntotal}"
    )

    return {

        "status": "success",

        "pdf": filename,

        "new_chunks": len(new_chunks),

        "total_chunks": len(chunks),

        "total_vectors": index.ntotal

    }


# =========================================================
# Search
# =========================================================

def search_documents(question):

    if index is None:

        return []

    query_vector = embedding_model.encode(

        ["query: " + question],

        normalize_embeddings=True

    )

    query_vector = np.asarray(
        query_vector,
        dtype="float32"
    )

    scores, indices = index.search(
        query_vector,
        MAX_RESULTS
    )

    results = []

    for score, idx in zip(
        scores[0],
        indices[0]
    ):

        if idx < 0:

            continue

        if score < SCORE_THRESHOLD:

            continue

        if idx >= len(metadata):

            continue

        item = metadata[idx]

        results.append({

            "score": float(score),

            "chunk_id": item["chunk_id"],

            "source": item["source"],

            "page": item["page"],

            "text": item["text"]

        })

    return results


# =========================================================
# Create Context
# =========================================================

def create_context(results):

    parts = []

    for item in results:

        parts.append(

            f"Source: {item['source']}\n"
            f"Page: {item['page']}\n"
            f"{item['text']}"

        )

    return "\n\n".join(
        parts
    )


# =========================================================
# Root
# =========================================================

@app.get("/")
def home():

    return {

        "message":
        "Windows RAG API is working"

    }


# =========================================================
# Search Endpoint
# =========================================================

@app.post("/search")
def search_api(
    data: Question
):

    results = search_documents(
        data.question
    )

    return {

        "question":
        data.question,

        "results":
        results

    }


# =========================================================
# Ask Endpoint
# =========================================================

@app.post("/ask")
def ask(
    data: Question
):

    # -----------------------------------------------------
    # Search
    # -----------------------------------------------------

    results = search_documents(
        data.question
    )

    if not results:

        return {

            "question":
            data.question,

            "answer":
            "متأسفم، اطلاعات مرتبطی پیدا نشد."

        }

    # -----------------------------------------------------
    # Create Context
    # -----------------------------------------------------

    context = create_context(
        results
    )

    # -----------------------------------------------------
    # Build Prompt
    # -----------------------------------------------------

    prompt = f"""
بر اساس اطلاعات زیر به سؤال کاربر پاسخ بده.

فقط از اطلاعات موجود در Context استفاده کن.
اگر پاسخ سؤال در Context وجود ندارد،
بگو اطلاعات کافی برای پاسخ وجود ندارد.

Context:
--------------------
{context}
--------------------

Question:
{data.question}
"""

    # -----------------------------------------------------
    # Send To Linux
    # -----------------------------------------------------

    response = requests.post(

        LINUX_API_URL,

        json={
            "question": prompt
        },

        timeout=120

    )

    response.raise_for_status()

    result = response.json()

    # -----------------------------------------------------
    # Return Answer
    # -----------------------------------------------------

    return {

        "question":
        data.question,

        "answer":
        result["results"]

    }


# =========================================================
# Upload PDF Endpoint
# =========================================================

@app.post("/upload-pdf")
async def upload_pdf(
    file: UploadFile = File(...)
):

    # -----------------------------------------------------
    # Validate file
    # -----------------------------------------------------

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No file selected."
        )

    if not file.filename.lower().endswith(
        ".pdf"
    ):

        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed."
        )

    # -----------------------------------------------------
    # Create folder
    # -----------------------------------------------------

    os.makedirs(
        PDF_FOLDER,
        exist_ok=True
    )

    # -----------------------------------------------------
    # Safe filename
    # -----------------------------------------------------

    filename = os.path.basename(
        file.filename
    )

    pdf_path = os.path.join(
        PDF_FOLDER,
        filename
    )

    # -----------------------------------------------------
    # Save file
    # -----------------------------------------------------

    try:

        with open(
            pdf_path,
            "wb"
        ) as output:

            while True:

                chunk = await file.read(
                    1024 * 1024
                )

                if not chunk:

                    break

                output.write(
                    chunk
                )

        # -------------------------------------------------
        # Add PDF to RAG
        # -------------------------------------------------

        result = process_pdf(
            pdf_path
        )

        return result

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:

        logger.exception(
            "Error while processing uploaded PDF."
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:

        await file.close()


# =========================================================
# Run
# =========================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(

        app,

        host="0.0.0.0",

        port=8000

    )
