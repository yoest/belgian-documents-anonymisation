from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ExtractedDocument:
    """Markdown of a PDF, with the original file kept for previews (in memory only)."""

    filename: str
    page_count: int
    text: str
    # Excluded from repr so the document never ends up in logs or tracebacks
    content: bytes = field(default=b"", repr=False)
