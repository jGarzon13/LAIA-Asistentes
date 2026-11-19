
def chunk_document(
    document: dict,
    max_words: int = 120,
    overlap_words: int = 20
) -> list[dict]:

    if max_words <= 0:
        raise ValueError("max_words debe ser positivo.")

    if not 0 <= overlap_words < max_words:
        raise ValueError(
            "overlap_words debe estar entre 0 y max_words - 1."
        )

    chunks = []
    chunk_number = 0
    step = max_words - overlap_words

    for section in document["sections"]:
        words = section["text"].split()

        for start in range(0, len(words), step):
            end = min(start + max_words, len(words))
            selected = words[start:end]

            if not selected:
                continue

            chunk_number += 1

           
            chunks.append({
                "id": f"{document['id']}-C{chunk_number:04d}",
                "document_id": document["id"],
                "filename": document["filename"],
                "page": section["page"],
                "text": " ".join(selected),
                "word_count": len(selected),
                "extraction_method": section.get(
                    "extraction_method", "text"
                ),
                "requires_review": section.get(
                    "requires_review", False
                )
            })


            if end == len(words):
                break

    return chunks
