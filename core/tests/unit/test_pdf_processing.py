import io

import pytest
from PIL import Image
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas

from belgian_anonymizer.config import AppConfig
from belgian_anonymizer.extraction import PdfExtractionError, PdfExtractor
from belgian_anonymizer.pipeline import AnonymizationPipeline
from tests.fixtures.contract_factory import ContractPdfFactory, SyntheticContract, french_lease
from tests.fixtures.sample_documents import formal_notice_fr


@pytest.fixture(scope="module")
def extractor(dev_config: AppConfig) -> PdfExtractor:
    return PdfExtractor(dev_config.extraction)


def canvas_pdf(*lines: str, encrypt: str | None = None, with_image: bool = False) -> bytes:
    canvas = Canvas(io.BytesIO(), pagesize=(595, 842), encrypt=encrypt)
    canvas.setFont("Helvetica", 10)
    for index, line in enumerate(lines):
        canvas.drawString(60, 780 - 14 * index, line)
    if with_image:
        # Textured like a photo or a scan: the layout model ignores flat colour blocks
        photo = Image.effect_noise((160, 120), 80).convert("RGB")
        canvas.drawImage(ImageReader(photo), 60, 480, 240, 180)
    # getpdfdata() finalises the document itself (calling save() first would encrypt twice)
    output: bytes = canvas.getpdfdata()
    return output


class TestPdfExtractor:
    def test_converts_a_contract_to_markdown(
        self, extractor: PdfExtractor, pdf_factory: ContractPdfFactory
    ) -> None:
        document = extractor.extract(pdf_factory.build(french_lease()), "bail.pdf")
        markdown = document.text

        assert document.page_count == 2
        # The centred title stays first (Docling alone moves it to the end of the page)
        assert markdown.lstrip("# ").startswith("CONTRAT DE BAIL DE RÉSIDENCE PRINCIPALE")
        assert "## Article 1" in markdown
        # Paragraphs come out as one line each, whatever their wrapping in the PDF
        assert "un appartement situé Chaussée de Waterloo 120, 1180 Uccle, comprenant" in markdown
        # Tables are kept as Markdown tables
        table_rows = [line for line in markdown.splitlines() if line.startswith("|")]
        assert any("1er septembre 2025" in row and "Jan Peeters" in row for row in table_rows)

    def test_images_are_replaced_by_a_marker(self, extractor: PdfExtractor) -> None:
        markdown = extractor.extract(
            canvas_pdf("Annexe : plan de l'appartement", with_image=True), "x.pdf"
        ).text
        assert "[IMAGE]" in markdown
        assert "Annexe : plan de l'appartement" in markdown

    def test_hyphen_at_a_line_break_is_kept(self, extractor: PdfExtractor) -> None:
        # Guards the Docling patch: Docling alone outputs "85.07.30033.28" and "1-ABC123"
        pdf = canvas_pdf(
            "Le locataire, inscrit au registre national sous le numéro 85.07.30-",
            "033.28, gare le véhicule immatriculé 1-ABC-",
            "123 sur l'emplacement prévu à cet effet par le présent contrat.",
        )
        markdown = extractor.extract(pdf, "x.pdf").text
        assert "85.07.30-033.28" in markdown
        assert "1-ABC-123" in markdown

    def test_grouped_paragraphs_are_split(self, extractor: PdfExtractor) -> None:
        # Short paragraphs on consecutive lines, as Docling groups them; the second one wraps
        pdf = canvas_pdf(
            "Entre les soussignés :",
            "Monsieur Jan Peeters, né à Louvain le 30 juillet 1985, domicilié Rue de la Loi 16, "
            "1000 Bruxelles,",
            "ci-après dénommé le Bailleur,",
            "Et :",
            "La société Immo Vandenberghe SRL, dont le siège est établi Avenue Louise 54, 1050 Ixelles,",
        )
        paragraphs = extractor.extract(pdf, "x.pdf").text.split("\n\n")
        assert "Et :" in paragraphs
        assert "Entre les soussignés :" in paragraphs

    def test_letter_address_blocks_keep_their_lines(
        self, extractor: PdfExtractor, pdf_factory: ContractPdfFactory
    ) -> None:
        # Docling merges the sender, recipient and date regions into one item: they are split again
        markdown = extractor.extract(pdf_factory.build(formal_notice_fr()), "lettre.pdf").text
        paragraphs = [paragraph.strip() for paragraph in markdown.split("\n\n")]
        recipient = next(p for p in paragraphs if p.startswith("Monsieur Kevin Janssens"))
        assert [line.strip() for line in recipient.splitlines()] == [
            "Monsieur Kevin Janssens",
            "Rue Haute 112",
            "1000 Bruxelles",
        ]
        assert "Bruxelles, le 14 octobre 2025" in paragraphs

    def test_rejects_non_pdf(self, extractor: PdfExtractor) -> None:
        with pytest.raises(PdfExtractionError, match="not a PDF"):
            extractor.extract(b"hello", "notes.txt")

    def test_rejects_pdf_without_text(self, extractor: PdfExtractor) -> None:
        with pytest.raises(PdfExtractionError, match="no text layer"):
            extractor.extract(canvas_pdf(with_image=True), "scan.pdf")

    def test_rejects_encrypted_pdf(self, extractor: PdfExtractor) -> None:
        with pytest.raises(PdfExtractionError, match="Password"):
            extractor.extract(canvas_pdf("Jan Peeters", encrypt="secret"), "locked.pdf")

    def test_rejects_corrupted_pdf(self, extractor: PdfExtractor) -> None:
        with pytest.raises(PdfExtractionError, match="corrupted"):
            extractor.extract(b"%PDF-1.7\n garbage", "broken.pdf")


class TestPatternPipeline:
    """End-to-end without NER: identifiers must be gone from the anonymised Markdown."""

    def test_identifiers_are_removed(
        self,
        pattern_pipeline: AnonymizationPipeline,
        pdf_factory: ContractPdfFactory,
        contract: SyntheticContract,
    ) -> None:
        result = pattern_pipeline.run(pdf_factory.build(contract), contract.filename)
        # Structured identifiers only (4+ digits or an e-mail): names and addresses need the NER model
        identifiers = [
            value
            for value in contract.sensitive_values
            if sum(c.isdigit() for c in value) >= 4 or "@" in value
        ]
        for value in identifiers:
            assert value not in result.anonymized_text
        for value in contract.kept_values:
            assert value in result.anonymized_text

    def test_values_in_tables_are_replaced(
        self, pattern_pipeline: AnonymizationPipeline, pdf_factory: ContractPdfFactory
    ) -> None:
        result = pattern_pipeline.run(pdf_factory.build(french_lease()), "bail.pdf")
        table_rows = [line for line in result.anonymized_text.splitlines() if line.startswith("|")]
        assert any("[IBAN_1]" in row for row in table_rows)
