import io
import logging

import pypdfium2 as pdfium
from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.exceptions import ConversionError
from docling_core.types.io import DocumentStream

from belgian_anonymizer.config import ExtractionConfig
from belgian_anonymizer.cpu import physical_core_estimate
from belgian_anonymizer.extraction.docling_patches import apply_docling_patches
from belgian_anonymizer.extraction.paragraph_splitter import ParagraphSplitter
from belgian_anonymizer.extraction.reading_order import ReadingOrderCorrector
from belgian_anonymizer.models.document import ExtractedDocument
from belgian_anonymizer.pdfium_lock import PDFIUM_LOCK

logger = logging.getLogger(__name__)


class PdfExtractionError(ValueError):
    """The uploaded file cannot be anonymised (not a PDF, encrypted, scanned, ...)."""


class PdfExtractor:
    """Converts a text-based PDF to Markdown with Docling: headings, paragraphs, lists and tables.

    Images are replaced by a marker (their content is not analysed), and page headers/footers
    are left out.
    """

    def __init__(self, config: ExtractionConfig) -> None:
        apply_docling_patches()
        self._image_placeholder = config.image_placeholder
        options = PdfPipelineOptions(
            artifacts_path=config.models_dir,
            accelerator_options=AcceleratorOptions(
                device=AcceleratorDevice.CPU,
                num_threads=config.threads or physical_core_estimate(),
            ),
            # Text-based PDFs only: no OCR, no page or picture images
            do_ocr=False,
            do_table_structure=config.table_structure,
            generate_page_images=False,
            generate_picture_images=False,
            document_timeout=config.timeout_seconds,
        )
        self._converter = DocumentConverter(
            format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options)}
        )
        self._reading_order = ReadingOrderCorrector()
        self._paragraphs = ParagraphSplitter()

    def warm_up(self) -> None:
        # Loads the layout and table models now rather than during the first user request
        self._converter.initialize_pipeline(InputFormat.PDF)

    def extract(self, content: bytes, filename: str) -> ExtractedDocument:
        if not content.lstrip()[:5] == b"%PDF-":
            raise PdfExtractionError("The file is not a PDF.")
        # Docling also relies on PDFium, which is not thread-safe
        with PDFIUM_LOCK:
            self._check_readable(content)
            try:
                result = self._converter.convert(DocumentStream(name=filename, stream=io.BytesIO(content)))
            except ConversionError as error:
                raise PdfExtractionError("The PDF file is corrupted or unreadable.") from error
            document = result.document
            self._paragraphs.split(document, content)

        self._reading_order.correct(document)
        markdown = document.export_to_markdown(
            # Raw text: escaping would alter the values to detect ("jan\\_peeters@...")
            escape_html=False,
            escape_underscores=False,
            image_placeholder=self._image_placeholder,
        )
        if not markdown.replace(self._image_placeholder, "").strip():
            raise PdfExtractionError("The PDF has no text layer (scanned documents are not supported yet).")
        return ExtractedDocument(filename, len(document.pages), markdown, content)

    @staticmethod
    def _check_readable(content: bytes) -> None:
        # Docling reports every failure the same way: check first, for a precise error message
        try:
            pdfium.PdfDocument(content).close()
        except pdfium.PdfiumError as error:
            if "password" in str(error).lower():
                raise PdfExtractionError("Password-protected PDFs are not supported.") from error
            raise PdfExtractionError("The PDF file is corrupted or unreadable.") from error
