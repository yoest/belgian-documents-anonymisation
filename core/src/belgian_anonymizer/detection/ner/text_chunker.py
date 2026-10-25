import re
from dataclasses import dataclass

_WORD = re.compile(r"\S+")


@dataclass(frozen=True, slots=True)
class TextChunk:
    offset: int
    text: str


class TextChunker:
    """Splits text into overlapping word windows that fit the NER model context (384 tokens for GLiNER)."""

    def __init__(self, chunk_size_words: int, overlap_words: int) -> None:
        if not 0 <= overlap_words < chunk_size_words:
            raise ValueError("overlap_words must be smaller than chunk_size_words")
        self._size = chunk_size_words
        self._step = chunk_size_words - overlap_words

    def split(self, text: str) -> list[TextChunk]:
        words = list(_WORD.finditer(text))
        chunks: list[TextChunk] = []
        for first in range(0, len(words), self._step):
            window = words[first : first + self._size]
            start, end = window[0].start(), window[-1].end()
            chunks.append(TextChunk(start, text[start:end]))
            if first + self._size >= len(words):
                break
        return chunks
