from pydantic import BaseModel, Field

from belgian_anonymizer.api.document_store import StoredDocument
from belgian_anonymizer.models.entity import EntityType
from belgian_anonymizer.models.mapping import MappingEntry


class EntitySchema(BaseModel):
    placeholder: str
    entity_type: EntityType
    text: str
    start: int = Field(description="Start offset in original_text")
    end: int = Field(description="End offset (exclusive) in original_text")
    score: float
    source: str


class MappingEntrySchema(BaseModel):
    placeholder: str
    entity_type: EntityType
    value: str
    variants: list[str] = Field(default_factory=list)

    @classmethod
    def from_entry(cls, entry: MappingEntry) -> "MappingEntrySchema":
        return cls(
            placeholder=entry.placeholder,
            entity_type=entry.entity_type,
            value=entry.value,
            variants=list(entry.variants),
        )

    def to_entry(self) -> MappingEntry:
        return MappingEntry(self.placeholder, self.entity_type, self.value, list(self.variants))


class AnonymizeResponse(BaseModel):
    document_id: str
    filename: str
    page_count: int
    processing_ms: int
    original_text: str
    anonymized_text: str
    entities: list[EntitySchema]
    mapping: list[MappingEntrySchema]

    @classmethod
    def from_stored(cls, stored: StoredDocument) -> "AnonymizeResponse":
        result = stored.result
        return cls(
            document_id=stored.document_id,
            filename=result.document.filename,
            page_count=result.document.page_count,
            processing_ms=result.processing_ms,
            original_text=result.document.text,
            anonymized_text=result.anonymized_text,
            entities=[
                EntitySchema(
                    placeholder=item.placeholder,
                    entity_type=item.entity.entity_type,
                    text=item.entity.text,
                    start=item.entity.start,
                    end=item.entity.end,
                    score=round(item.entity.score, 4),
                    source=item.entity.source,
                )
                for item in result.entities
            ],
            mapping=[MappingEntrySchema.from_entry(entry) for entry in result.mapping.entries],
        )


class DocumentDeanonymizeRequest(BaseModel):
    text: str = Field(description="Text containing placeholders, typically the LLM answer")


class DeanonymizeRequest(DocumentDeanonymizeRequest):
    mapping: list[MappingEntrySchema]


class DeanonymizeResponse(BaseModel):
    text: str
    replaced_count: int
    unknown_placeholders: list[str]


class HealthResponse(BaseModel):
    status: str
    ner_enabled: bool


class ErrorResponse(BaseModel):
    detail: str
