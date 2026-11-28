import re


def normalize_text(text: str) -> str:

    text = text.replace("\x00", "")

    text = re.sub(r"[ \t]+", " ", text)

    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def chunk_text(
    text: str,
    chunk_size: int = 250,
    overlap: int = 40
) -> list[str]:

    if chunk_size <= 0:
        raise ValueError("Chunk size must be positive.")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("Invalid chunk overlap.")

    text = normalize_text(text)

    words = text.split()

    if not words:
        return []

    chunks = []

    step = chunk_size - overlap

    for start in range(0, len(words), step):

        end = start + chunk_size

        chunk = " ".join(words[start:end])

        if chunk:
            chunks.append(chunk)

        if end >= len(words):
            break

    return chunks