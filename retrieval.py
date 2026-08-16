from sentence_transformers import SentenceTransformer
import faiss
import json
import os


os.system("cls")


# ==========================================
# 1. بارگذاری مدل Embedding
# ==========================================

print("Loading retrieval model...")

model = SentenceTransformer(
    "intfloat/multilingual-e5-small"
)

print("Model loaded!")


# ==========================================
# 2. بارگذاری FAISS Index
# ==========================================

print("Loading FAISS index...")

index = faiss.read_index(
    "vector_store/catalog.index"
)

print(f"FAISS vectors: {index.ntotal}")


# ==========================================
# 3. بارگذاری Metadata
# ==========================================

print("Loading metadata...")

with open(
    "vector_store/metadata.json",
    "r",
    encoding="utf-8"
) as f:
    metadata = json.load(f)

print(f"Metadata records: {len(metadata)}")


# ==========================================
# 4. تابع جستجو
# ==========================================

def search(question):

    # آماده کردن سؤال برای مدل E5
    query = "query: " + question

    # ساخت Embedding سؤال
    query_embedding = model.encode(
        [query],
        normalize_embeddings=True
    )

    # جستجو در FAISS
    scores, indices = index.search(
        query_embedding,
        5
    )

    results = []

    # بررسی نتایج پیدا شده
    for score, idx in zip(scores[0], indices[0]):

        # حذف نتیجه نامعتبر
        if idx < 0:
            continue

        # حذف نتایج با امتیاز پایین
        if score < 0.75:
            continue

        # گرفتن اطلاعات Chunk
        item = metadata[idx]

        # اضافه کردن نتیجه
        results.append({
            "chunk_id": item["chunk_id"],
            "source": item["source"],
            "page": item["page"],
            "text": item["text"],
            "score": float(score)
        })

    return results


# ==========================================
# 5. ساخت Context برای LLM
# ==========================================

def create_context(results):

    context = ""

    for item in results:
        context += item["text"] + "\n\n"

    return context
