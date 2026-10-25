import io
from dataclasses import dataclass, field
from xml.sax.saxutils import escape

from PIL import Image as PilImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    Flowable,
    Image,
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# All people, companies and numbers below are fictitious; numbers only have valid checksums


class SyntheticIdentifiers:
    """Builds fake Belgian identifiers with valid check digits."""

    @staticmethod
    def national_number(birth_date: str, sequence: str, born_after_2000: bool = False) -> str:
        base = birth_date + sequence
        check = 97 - int(("2" if born_after_2000 else "") + base) % 97
        return f"{base[:2]}.{base[2:4]}.{base[4:6]}-{base[6:9]}.{check:02d}"

    @staticmethod
    def enterprise_number(first_eight_digits: str) -> str:
        digits = first_eight_digits + f"{97 - int(first_eight_digits) % 97:02d}"
        return f"BE {digits[:4]}.{digits[4:7]}.{digits[7:]}"

    @staticmethod
    def mod97_remainder_number(first_ten_digits: str) -> str:
        return first_ten_digits + f"{int(first_ten_digits) % 97 or 97:02d}"

    @classmethod
    def belgian_iban(cls, first_ten_digits: str) -> str:
        bban = cls.mod97_remainder_number(first_ten_digits)
        # "BE" = 11 14 in the IBAN letter-to-digit conversion
        check = 98 - int(bban + "111400") % 97
        iban = f"BE{check:02d}{bban}"
        return " ".join(iban[i : i + 4] for i in range(0, len(iban), 4))

    @classmethod
    def id_card_number(cls, first_ten_digits: str) -> str:
        digits = cls.mod97_remainder_number(first_ten_digits)
        return f"{digits[:3]}-{digits[3:10]}-{digits[10:]}"


@dataclass(frozen=True)
class Borderless:
    """Table without borders, as used for address and signature blocks."""

    rows: list[list[str]]


# A block is a paragraph or a table. Paragraph prefixes: "# " centred title, "## " heading,
# "- " bullet item, ">> " right-aligned; "[IMAGE]" alone is a picture (e.g. a logo)
Block = str | list[list[str]] | Borderless
IMAGE_BLOCK = "[IMAGE]"


@dataclass
class SyntheticContract:
    filename: str
    blocks: list[Block]
    # Values that must not survive anonymisation
    sensitive_values: list[str]
    # Values that must stay in clear text (they are useful to the LLM)
    kept_values: list[str] = field(default_factory=list)
    # Repeated on every page (letterhead, company details)
    header: str | None = None
    footer: str | None = None


class ContractPdfFactory:
    """Renders a synthetic contract as a word-processor-like A4 PDF (title, headings, tables)."""

    _MARGIN = 60

    def __init__(self) -> None:
        styles = getSampleStyleSheet()
        self._title = ParagraphStyle("ContractTitle", parent=styles["Title"], fontSize=14)
        self._heading = ParagraphStyle("ContractHeading", parent=styles["Heading3"], spaceBefore=10)
        self._body = ParagraphStyle("ContractBody", parent=styles["BodyText"], alignment=TA_JUSTIFY)
        self._right = ParagraphStyle("ContractRight", parent=self._body, alignment=TA_RIGHT)

    def build(self, contract: SyntheticContract) -> bytes:
        output = io.BytesIO()
        document = SimpleDocTemplate(
            output,
            pagesize=A4,
            leftMargin=self._MARGIN,
            rightMargin=self._MARGIN,
            topMargin=self._MARGIN,
            bottomMargin=self._MARGIN,
        )
        flowables: list[Flowable] = []
        bullets: list[str] = []
        for block in [*contract.blocks, ""]:
            # Consecutive "- " paragraphs form one bulleted list
            if isinstance(block, str) and block.startswith("- "):
                bullets.append(block[2:])
                continue
            if bullets:
                items = [ListItem(Paragraph(escape(item), self._body)) for item in bullets]
                flowables.append(ListFlowable(items, bulletType="bullet", leftIndent=14))
                bullets = []
            if block:
                flowables.extend(self._flowables(block))

        def decorate(canvas: Canvas, _document: SimpleDocTemplate) -> None:
            canvas.setFont("Helvetica", 8)
            width, height = A4
            if contract.header:
                canvas.drawCentredString(width / 2, height - 30, contract.header)
            if contract.footer:
                canvas.drawCentredString(width / 2, 30, contract.footer)

        document.build(flowables, onFirstPage=decorate, onLaterPages=decorate)
        return output.getvalue()

    def _cell(self, text: str) -> Paragraph:
        return Paragraph(escape(text).replace("\n", "<br/>"), self._body)

    def _flowables(self, block: Block) -> list[Flowable]:
        if isinstance(block, Borderless):
            return [Table([[self._cell(cell) for cell in row] for row in block.rows])]
        if isinstance(block, list):
            table = Table([[self._cell(cell) for cell in row] for row in block])
            table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.grey)]))
            return [table, Spacer(1, 8)]
        if block == IMAGE_BLOCK:
            # Textured like a real logo or scan: the layout model ignores flat colour blocks
            picture = io.BytesIO()
            PilImage.effect_noise((160, 80), 60).convert("RGB").save(picture, format="PNG")
            picture.seek(0)
            return [Image(picture, width=120, height=60, hAlign="LEFT"), Spacer(1, 8)]
        if block.startswith(">> "):
            return [Paragraph(escape(block[3:]).replace("\n", "<br/>"), self._right)]
        if block.startswith("# "):
            return [Paragraph(escape(block[2:]), self._title)]
        if block.startswith("## "):
            return [Paragraph(escape(block[3:]), self._heading)]
        return [Paragraph(escape(block).replace("\n", "<br/>"), self._body)]


def french_lease() -> SyntheticContract:
    ids = SyntheticIdentifiers
    niss = ids.national_number("850730", "033")
    enterprise = ids.enterprise_number("07123456")
    iban = ids.belgian_iban("3630123456")
    id_card = ids.id_card_number("5921234567")
    filler = (
        "Le Preneur s'engage à occuper les lieux en bon père de famille et à les restituer dans l'état "
        "où il les a reçus, compte tenu de l'usure normale. Toute modification des lieux loués requiert "
        "l'accord écrit préalable du Bailleur. "
    )
    return SyntheticContract(
        filename="contrat-de-bail-fr.pdf",
        blocks=[
            "# CONTRAT DE BAIL DE RÉSIDENCE PRINCIPALE",
            "Entre les soussignés :",
            f"Monsieur Jan Peeters, né à Louvain le 30 juillet 1985, numéro de registre national {niss}, "
            "domicilié Rue de la Loi 16, 1000 Bruxelles, téléphone +32 470 12 34 56, "
            "e-mail jan.peeters@example.be, ci-après dénommé « le Bailleur »,",
            "Et :",
            "La société Immo Vandenberghe SRL, dont le siège est établi Avenue Louise 54, 1050 Ixelles, "
            f"inscrite à la Banque-Carrefour des Entreprises sous le numéro {enterprise}, représentée par "
            f"Madame Sophie Dubois, gérante, titulaire de la carte d'identité n° {id_card}, "
            "ci-après dénommée « le Preneur »,",
            "Il est convenu ce qui suit :",
            "## Article 1 – Objet",
            "Le Bailleur donne en location au Preneur, qui accepte, un appartement situé "
            "Chaussée de Waterloo 120, 1180 Uccle, comprenant deux chambres, une cuisine et une cave.",
            "## Article 2 – Durée",
            "Le bail est conclu pour une durée de neuf ans prenant cours le 1er septembre 2025. "
            "Il peut être résilié par le Preneur moyennant un préavis de trois mois.",
            "## Article 3 – Loyer",
            "Le loyer mensuel est fixé à 1.250 euros, payable par virement selon l'échéancier suivant :",
            [
                ["Échéance", "Montant", "Compte", "Titulaire"],
                ["1er septembre 2025", "1.250 euros", iban, "Jan Peeters"],
                ["1er octobre 2025", "1.250 euros", iban, "Jan Peeters"],
            ],
            "## Article 4 – Garantie locative",
            "Le Preneur constitue une garantie de 2.500 euros sur un compte bloqué ouvert à son nom.",
            "## Article 5 – Parking",
            "Un emplacement de parking n° 3 est mis à disposition pour le véhicule immatriculé 1-ABC-123.",
            *[block for number in range(6, 12) for block in (f"## Article {number} – Entretien", filler * 3)],
            "## Article 12 – Correspondance",
            "Toute notification au Bailleur est adressée à M. Peeters à son domicile. "
            "Toute notification à Immo Vandenberghe est adressée à son siège.",
            "Fait à Bruxelles, le 1er septembre 2025, en deux exemplaires originaux.",
            [["Le Bailleur, Jan PEETERS", "Pour le Preneur, Sophie DUBOIS"]],
        ],
        sensitive_values=[
            "Jan Peeters",
            "Peeters",
            "PEETERS",
            "30 juillet 1985",
            niss,
            "Rue de la Loi 16",
            "+32 470 12 34 56",
            "jan.peeters@example.be",
            "Immo Vandenberghe",
            "Avenue Louise 54",
            enterprise,
            "Sophie Dubois",
            "DUBOIS",
            id_card,
            "Chaussée de Waterloo 120",
            iban,
            "1-ABC-123",
        ],
        kept_values=["le Bailleur", "le Preneur", "1.250 euros", "1er septembre 2025", "Monsieur", "Madame"],
    )


def dutch_lease() -> SyntheticContract:
    ids = SyntheticIdentifiers
    niss = ids.national_number("020315", "122", born_after_2000=True)
    iban = ids.belgian_iban("0011234567")
    enterprise = ids.enterprise_number("08765432")
    return SyntheticContract(
        filename="huurovereenkomst-nl.pdf",
        blocks=[
            "# HUUROVEREENKOMST VOOR HOOFDVERBLIJFPLAATS",
            "Tussen:",
            f"Mevrouw Marie De Smet, geboren te Gent op 15/03/2002, rijksregisternummer {niss}, wonende te "
            "Kerkstraat 5 bus 2, 9000 Gent, telefoon 09 123 45 67, e-mail marie.desmet@example.be, "
            'hierna genoemd "de Verhuurder",',
            "En:",
            "De heer Pieter Janssens, zaakvoerder van Bakkerij Janssens BV, ondernemingsnummer "
            f"{enterprise}, wonende Grote Markt 1, 2000 Antwerpen, IBAN {iban}, "
            'hierna genoemd "de Huurder",',
            "Wordt overeengekomen wat volgt:",
            "## Artikel 1 – Voorwerp",
            "De Verhuurder verhuurt aan de Huurder een woning gelegen te Veldstraat 42, 9000 Gent.",
            "## Artikel 2 – Huurprijs",
            "De maandelijkse huurprijs bedraagt 950 euro, te betalen voor de vijfde van elke maand.",
            "## Artikel 3 – Duur",
            "De huur wordt gesloten voor een periode van drie jaar vanaf 1 oktober 2025.",
            "Opgemaakt te Gent op 1 oktober 2025 in twee exemplaren.",
            [["De Verhuurder, M. De Smet", "De Huurder, P. JANSSENS"]],
        ],
        sensitive_values=[
            "Marie De Smet",
            "Smet",
            "15/03/2002",
            niss,
            "Kerkstraat 5",
            "09 123 45 67",
            "marie.desmet@example.be",
            "Pieter Janssens",
            "JANSSENS",
            enterprise,
            "Grote Markt 1",
            iban,
            "Veldstraat 42",
        ],
        kept_values=["de Verhuurder", "de Huurder", "950 euro", "1 oktober 2025"],
    )
