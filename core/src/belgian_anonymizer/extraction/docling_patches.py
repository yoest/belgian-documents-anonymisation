from docling.models.stages.page_assemble.page_assemble_model import PageAssembleModel

_SOFT_HYPHEN = "­"
_original_sanitize_text = PageAssembleModel.sanitize_text


def _sanitize_text_keeping_hyphens(self: PageAssembleModel, lines: list[str]) -> str:
    """Joins lines ending with a hyphen without dropping it.

    Docling treats "85.07.30-" + "033.28" as a hyphenated word and outputs "85.07.30033.28",
    which corrupts identifiers and compound names. Business documents rarely use automatic
    hyphenation, so a visible hyphen is kept; only a soft hyphen (real hyphenation) is removed.
    """
    merged: list[str] = []
    for line in lines:
        if merged and merged[-1].endswith(_SOFT_HYPHEN):
            merged[-1] = merged[-1][:-1] + line
        elif merged and len(merged[-1]) > 1 and merged[-1].endswith("-") and merged[-1][-2].isalnum():
            merged[-1] += line
        else:
            merged.append(line)
    text: str = _original_sanitize_text(self, merged)
    return text


def apply_docling_patches() -> None:
    # Idempotent: the extractor may be created several times (tests, reloads)
    PageAssembleModel.sanitize_text = _sanitize_text_keeping_hyphens  # type: ignore[method-assign]
