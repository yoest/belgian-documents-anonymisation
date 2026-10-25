import re
from abc import ABC, abstractmethod
from typing import ClassVar

from belgian_anonymizer.models.entity import DetectedEntity, EntityType


class EntityPriority:
    """Overlap resolution order: a checksum-validated identifier beats an NER guess."""

    PROPAGATED = 5
    CONTEXTUAL = 10
    FORMAT = 20
    CHECKSUM = 30


class BaseRecognizer(ABC):
    @property
    def name(self) -> str:
        return type(self).__name__

    @abstractmethod
    def recognize(self, text: str) -> list[DetectedEntity]: ...


class PatternRecognizer(BaseRecognizer):
    """Regex recognizer; a named group `value` restricts the entity to part of the match."""

    entity_type: ClassVar[EntityType]
    patterns: ClassVar[tuple[re.Pattern[str], ...]]
    score: ClassVar[float] = 0.9
    priority: ClassVar[int] = EntityPriority.FORMAT

    def validate(self, value: str) -> bool:
        return True

    def resolve_type(self, text: str, start: int) -> EntityType:
        return self.entity_type

    def recognize(self, text: str) -> list[DetectedEntity]:
        entities: list[DetectedEntity] = []
        for pattern in self.patterns:
            for match in pattern.finditer(text):
                group = "value" if "value" in pattern.groupindex else 0
                start, end = match.span(group)
                value = text[start:end]
                if not self.validate(value):
                    continue
                entities.append(
                    DetectedEntity(
                        entity_type=self.resolve_type(text, start),
                        start=start,
                        end=end,
                        text=value,
                        score=self.score,
                        source=self.name,
                        priority=self.priority,
                    )
                )
        return entities
