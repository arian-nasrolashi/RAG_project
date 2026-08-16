from sentence_transformers import SentenceTransformer
import faiss
import json
import os

os.system("cls")

# ==========================================
# 1. Load embedding model
# ==========================================

print("Loading model...")

model = SentenceTransformer("intfloat/multilingual-e5-small")

print("Model loaded!")

# ==========================================
# 2. Load FAISS index
# ==========================================

print("\nLoading FAISS index...")

index = faiss.read_index(
    "vector_store/catalog.index"
)

print(f"FAISS vectors: {index.ntotal}")

# ==========================================
# 3. Load metadata
# ==========================================

print("\nLoading metadata...")

with open(
    "vector_store/metadata.json",
    "r",
    encoding="utf-8"
) as f:

    metadata = json.load(f)

print(f"Metadata records: {len(metadata)}")

# ==========================================
# 4. Ask question
# ==========================================

question = input("\nAsk a question: ")

query = "query: " + question

# ==========================================
# 5. Create query embedding
# ==========================================

query_embedding = model.encode(
    [query],
    normalize_embeddings=True
)

# ==========================================
# 6. FAISS Search
# ==========================================

# تعداد نتایج اولیه
k = 5

scores, indices = index.search(
    query_embedding,
    k
)

# ==========================================
# 7. Similarity Threshold
# ==========================================

threshold = 0.75

# ==========================================
# 8. Show results
# ==========================================

print("\n" + "=" * 60)
print("SEARCH RESULTS")
print("=" * 60)

found_results = 0

for rank, (score, idx) in enumerate(
    zip(scores[0], indices[0]),
    start=1
):

    # اگر نتیجه نامعتبر بود
    if idx < 0:
        continue

    # اگر similarity پایین بود
    if score < threshold:
        continue

    item = metadata[idx]

    found_results += 1

    print(f"\nResult #{found_results}")
    print(f"Similarity: {score:.4f}")
    print(f"Chunk ID: {item['chunk_id']}")
    print(f"Source: {item['source']}")
    print(f"Page: {item['page']}")
    print("-" * 60)
    print(item["text"])
    print("=" * 60)

# ==========================================
# 9. No results
# ==========================================

if found_results == 0:

    print("\nNo sufficiently relevant results found.")

    print(
        f"All results had similarity below {threshold}."
    )
