from dataclasses import dataclass, replace
from enum import StrEnum


class EntityType(StrEnum):
    PERSON = "PERSON"
    ORGANIZATION = "ORGANIZATION"
    ADDRESS = "ADDRESS"
    NATIONAL_NUMBER = "NATIONAL_NUMBER"
    ENTERPRISE_NUMBER = "ENTERPRISE_NUMBER"
    IBAN = "IBAN"
    ID_CARD_NUMBER = "ID_CARD_NUMBER"
    PHONE = "PHONE"
    EMAIL = "EMAIL"
    LICENSE_PLATE = "LICENSE_PLATE"
    DATE_OF_BIRTH = "DATE_OF_BIRTH"


@dataclass(frozen=True, slots=True)
class DetectedEntity:
    """A span of the document text identified as personal data. `end` is exclusive."""

    entity_type: EntityType
    start: int
    end: int
    text: str
    score: float
    source: str
    # Higher priority wins overlaps: checksum-validated identifiers beat NER guesses
    priority: int = 0
    # For propagated name parts ("Peeters"), the full form they belong to ("Jan Peeters")
    canonical_text: str | None = None

    @property
    def length(self) -> int:
        return self.end - self.start

    def overlaps(self, other: "DetectedEntity") -> bool:
        return self.start < other.end and other.start < self.end

    def with_span(self, start: int, end: int, text: str) -> "DetectedEntity":
        return replace(self, start=start, end=end, text=text)


@dataclass(frozen=True, slots=True)
class AnonymizedEntity:
    """A detected entity together with the placeholder that replaced it."""

    entity: DetectedEntity
    placeholder: str
