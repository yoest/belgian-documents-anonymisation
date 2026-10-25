from dataclasses import dataclass

from belgian_anonymizer.models.document import ExtractedDocument
from belgian_anonymizer.models.entity import AnonymizedEntity
from belgian_anonymizer.models.mapping import AnonymizationMapping


@dataclass(frozen=True, slots=True)
class AnonymizationResult:
    document: ExtractedDocument
    anonymized_text: str
    entities: list[AnonymizedEntity]
    mapping: AnonymizationMapping
    processing_ms: int
