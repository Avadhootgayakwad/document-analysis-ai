from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.services.chunking_service import chunk_text


def retrieve_context(
    question: str,
    documents: list[dict],
    top_k: int = 5
) -> list[dict]:

    if not question.strip():
        return []

    chunks = []

    for document in documents:

        text = document.get("text") or ""

        document_chunks = chunk_text(text)

        for index, content in enumerate(document_chunks):

            chunks.append({
                "document_id": document["id"],
                "filename": document["filename"],
                "chunk_index": index,
                "content": content
            })

    if not chunks:
        return []

    texts = [
        chunk["content"]
        for chunk in chunks
    ]

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        max_features=15000,
        token_pattern=r"(?u)\b\w+\b"
    )

    try:

        matrix = vectorizer.fit_transform(texts)

        question_vector = vectorizer.transform(
            [question]
        )

    except ValueError:
        return []

    scores = cosine_similarity(
        question_vector,
        matrix
    ).flatten()

    ranked_indices = scores.argsort()[::-1]

    results = []

    for index in ranked_indices:

        score = float(scores[index])

        if score <= 0:
            continue

        result = chunks[index].copy()

        result["relevance_score"] = round(score, 4)

        results.append(result)

        if len(results) >= top_k:
            break

    return results


def build_context(results: list[dict]) -> str:

    sections = []

    for index, result in enumerate(results):

        sections.append(
            f"[Source {index + 1}]\n"
            f"Document: {result['filename']}\n"
            f"Chunk: {result['chunk_index'] + 1}\n"
            f"Content:\n{result['content']}"
        )

    return "\n\n".join(sections)