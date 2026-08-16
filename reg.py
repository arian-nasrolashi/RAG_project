import os
import re
import json
import pymupdf
from PIL import Image
import pytesseract
from langchain_text_splitters import RecursiveCharacterTextSplitter

os.system("cls")

# ==========================================
# 1. مسیر PDFها
# ==========================================

PDF_FOLDER = r"C:\Users\user\Documents\pdf.13"

# ==========================================
# 2. پیدا کردن PDFها
# ==========================================

pdf_files = [
    file
    for file in os.listdir(PDF_FOLDER)
    if file.lower().endswith(".pdf")
]

pdf_files.sort()

print(f"PDF files found: {len(pdf_files)}")

for file in pdf_files:
    print(f" - {file}")

# ==========================================
# 3. Text Splitter
# ==========================================

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=[
        "\n\n",
        "\n",
        " ",
        ""
    ]
)

# ==========================================
# 4. تابع پاکسازی متن
# ==========================================


def clean_text(text):

    # حذف فاصله‌های اضافی
    text = re.sub(r"[ \t]+", " ", text)

    # حذف خطوط خالی اضافی
    text = re.sub(
        r"\n\s*\n+",
        "\n\n",
        text
    )

    # حذف فاصله قبل از علائم نگارشی
    text = re.sub(
        r"\s+([،؛:,.!?؟])",
        r"\1",
        text
    )

    # اضافه کردن فاصله بعد از بعضی علائم
    text = re.sub(
        r"([،؛:])(?=\S)",
        r"\1 ",
        text
    )

    return text.strip()


# ==========================================
# 5. تابع OCR
# ==========================================

def ocr_page(page):

    pix = page.get_pixmap(
        matrix=pymupdf.Matrix(2, 2)
    )

    img = Image.frombytes(
        "RGB",
        [pix.width, pix.height],
        pix.samples
    )

    text = pytesseract.image_to_string(
        img,
        lang="fas+eng"
    )

    return text


# ==========================================
# 6. استخراج و ساخت Chunk
# ==========================================

chunks = []

chunk_id = 0

for pdf_index, filename in enumerate(pdf_files, start=1):

    pdf_path = os.path.join(
        PDF_FOLDER,
        filename
    )

    print("\n" + "=" * 60)
    print(f"Processing PDF {pdf_index}/{len(pdf_files)}")
    print(f"File: {filename}")
    print("=" * 60)

    doc = pymupdf.open(pdf_path)

    print(f"Pages: {len(doc)}")

    for page_number, page in enumerate(doc, start=1):

        page_text = ocr_page(page)

        if not page_text.strip():
            continue

        # پاکسازی متن
        page_text = clean_text(page_text)

        # ==================================
        # 7. ساخت Chunk
        # ==================================

        page_chunks = splitter.split_text(page_text)

        for chunk in page_chunks:

            cleaned_chunk = clean_text(chunk)

            # حذف Chunkهای خیلی کوتاه
            if len(cleaned_chunk) < 50:
                continue

            # حذف Chunkهایی که فقط عدد هستند
            if cleaned_chunk.isdigit():
                continue

            chunks.append({
                "chunk_id": chunk_id,
                "source": filename,
                "page": page_number,
                "text": cleaned_chunk
            })

            chunk_id += 1

    doc.close()
# ==========================================
# 8. نتیجه
# ==========================================

print("\n" + "=" * 60)
print("CHUNKING COMPLETED")
print("=" * 60)

print(f"Total PDFs: {len(pdf_files)}")
print(f"Total chunks: {len(chunks)}")


# ==========================================
# 9. نمایش چند Chunk برای بررسی
# ==========================================

if chunks:

    print("\n" + "=" * 60)
    print("SAMPLE CHUNKS")
    print("=" * 60)

    for chunk in chunks[:5]:

        print("\n" + "-" * 60)
        print(f"Chunk ID: {chunk['chunk_id']}")
        print(f"Source: {chunk['source']}")
        print(f"Page: {chunk['page']}")
        print("-" * 60)
        print(chunk["text"])

else:

    print("\nWARNING: No chunks were created!")


# ==========================================
# 10. ذخیره chunks.json
# ==========================================

with open(
    "chunks.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        chunks,
        f,
        ensure_ascii=False,
        indent=2
    )

print("\nChunks saved successfully!")
print("File: chunks.json")
