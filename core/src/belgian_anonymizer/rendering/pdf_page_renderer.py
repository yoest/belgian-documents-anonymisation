import io

import pypdfium2 as pdfium

from belgian_anonymizer.pdfium_lock import PDFIUM_LOCK

_POINTS_PER_INCH = 72


class PageOutOfRangeError(IndexError):
    pass


class PdfPageRenderer:
    """Renders one page of the original PDF as a PNG image, so clients need no PDF viewer."""

    def __init__(self, dpi: int) -> None:
        self._scale = dpi / _POINTS_PER_INCH

    def render_png(self, content: bytes, page_number: int) -> bytes:
        with PDFIUM_LOCK:
            pdf = pdfium.PdfDocument(content)
            try:
                if not 0 <= page_number < len(pdf):
                    raise PageOutOfRangeError(page_number)
                page = pdf[page_number]
                try:
                    image = page.render(scale=self._scale).to_pil()
                finally:
                    page.close()
            finally:
                pdf.close()
        output = io.BytesIO()
        image.save(output, format="PNG", optimize=True)
        return output.getvalue()
