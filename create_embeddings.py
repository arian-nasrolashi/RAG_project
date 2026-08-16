from sentence_transformers import SentenceTransformer
import time
import json
import os

os.system("cls")


# ==========================================
# 1. بارگذاری مدل Embedding
# ==========================================

print("Loading embedding model...")

model = SentenceTransformer(
    "intfloat/multilingual-e5-small"
)

print("Model loaded successfully!")


# ==========================================
# 2. خواندن chunks.json
# ==========================================

print("\nLoading chunks.json...")

with open(
    "chunks.json",
    "r",
    encoding="utf-8"
) as f:
    chunks = json.load(f)

print(f"Number of chunks: {len(chunks)}")


# ==========================================
# 3. آماده کردن متن‌ها
# ==========================================

texts = []

for chunk in chunks:

    texts.append(
        "passage: " + chunk["text"]
    )


# ==========================================
# 4. ساخت Embedding
# ==========================================

print("\nCreating embeddings...")

start_time = time.time()

embeddings = model.encode(
    texts,
    batch_size=8,
    show_progress_bar=True,
    normalize_embeddings=True
)

end_time = time.time()

print("\nEmbedding completed!")
print(
    f"Time: {end_time - start_time:.2f} seconds"
)


# ==========================================
# 5. ساخت خروجی
# ==========================================

results = []

for chunk, embedding in zip(chunks, embeddings):

    results.append({
        "chunk_id": chunk["chunk_id"],
        "source": chunk["source"],
        "page": chunk["page"],
        "text": chunk["text"],
        "embedding": embedding.tolist()
    })


# ==========================================
# 6. ذخیره Embeddingها
# ==========================================

with open(
    "embeddings.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        results,
        f,
        ensure_ascii=False,
        indent=2
    )


# ==========================================
# 7. بررسی نتیجه
# ==========================================

print("\nEmbeddings saved successfully!")

print(
    f"Total embeddings: {len(results)}"
)

print(
    f"Embedding dimensions: "
    f"{len(results[0]['embedding'])}"
)

print("\nFirst embedding:")
print(
    results[0]["embedding"][:10]
)
