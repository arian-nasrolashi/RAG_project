import os
import json
import numpy as np
import faiss

os.system("cls")

# ==========================================
# 1. خواندن Embeddings
# ==========================================

print("Loading embeddings.json...")

with open("embeddings.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Number of embeddings: {len(data)}")

# ==========================================
# 2. تبدیل Embeddingها به NumPy
# ==========================================

vectors = np.array(
    [item["embedding"] for item in data],
    dtype="float32"
)

print(f"Vector shape: {vectors.shape}")

# ==========================================
# 3. ساخت FAISS Index
# ==========================================

dimension = vectors.shape[1]

index = faiss.IndexFlatIP(dimension)

index.add(vectors)

print(f"Vectors stored in FAISS: {index.ntotal}")

# ==========================================
# 4. ساخت پوشه Vector Store
# ==========================================

os.makedirs("vector_store", exist_ok=True)

# ==========================================
# 5. ذخیره FAISS
# ==========================================

faiss.write_index(
    index,
    "vector_store/catalog.index"
)

# ==========================================
# 6. ذخیره Metadata
# ==========================================

metadata = []

for item in data:
    metadata.append({
        "chunk_id": item["chunk_id"],
        "source": item["source"],
        "page": item["page"],
        "text": item["text"]
    })

with open(
    "vector_store/metadata.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(
        metadata,
        f,
        ensure_ascii=False,
        indent=2
    )

# ==========================================
# 7. نتیجه
# ==========================================

print("\nFAISS index saved successfully!")
print("File: vector_store/catalog.index")

print("\nMetadata saved successfully!")
print("File: vector_store/metadata.json")
