import re
from collections import Counter

from belgian_anonymizer.models.entity import AnonymizedEntity, DetectedEntity, EntityType
from belgian_anonymizer.models.mapping import AnonymizationMapping, MappingEntry

_IDENTIFIER_TYPES = {
    EntityType.NATIONAL_NUMBER,
    EntityType.ENTERPRISE_NUMBER,
    EntityType.IBAN,
    EntityType.ID_CARD_NUMBER,
    EntityType.PHONE,
    EntityType.LICENSE_PLATE,
}
_NON_ALNUM = re.compile(r"[^0-9A-Za-z]")
_NON_WORD = re.compile(r"[\W_]+")


class Pseudonymizer:
    """Replaces entities by numbered placeholders ([PERSON_1], [IBAN_2]...) and builds the reverse mapping.

    The same value always gets the same placeholder, so the LLM can still tell parties apart.
    """

    def anonymize(
        self, text: str, entities: list[DetectedEntity]
    ) -> tuple[str, list[AnonymizedEntity], AnonymizationMapping]:
        mapping = AnonymizationMapping()
        placeholders: dict[tuple[EntityType, str], str] = {}
        counters: Counter[EntityType] = Counter()
        anonymized: list[AnonymizedEntity] = []

        for entity in sorted(entities, key=lambda e: e.start):
            key = (
                entity.entity_type,
                self._normalize(entity.entity_type, entity.canonical_text or entity.text),
            )
            placeholder = placeholders.get(key)
            if placeholder is None:
                counters[entity.entity_type] += 1
                placeholder = f"[{entity.entity_type}_{counters[entity.entity_type]}]"
                placeholders[key] = placeholder
                value = " ".join((entity.canonical_text or entity.text).split())
                mapping.add(MappingEntry(placeholder, entity.entity_type, value))
            entry = mapping.get(placeholder)
            if entry is not None:
                entry.add_variant(" ".join(entity.text.split()))
            anonymized.append(AnonymizedEntity(entity, placeholder))

        return self._replace(text, anonymized), anonymized, mapping

    @staticmethod
    def _normalize(entity_type: EntityType, value: str) -> str:
        # "BE68 5390 0754 7034" and "BE68539007547034" are the same account,
        # "PEETERS" and "Peeters" the same name
        if entity_type in _IDENTIFIER_TYPES:
            return _NON_ALNUM.sub("", value).upper()
        return _NON_WORD.sub(" ", value).strip().casefold()

    @staticmethod
    def _replace(text: str, anonymized: list[AnonymizedEntity]) -> str:
        pieces: list[str] = []
        cursor = 0
        for item in anonymized:
            pieces.append(text[cursor : item.entity.start])
            pieces.append(item.placeholder)
            cursor = item.entity.end
        pieces.append(text[cursor:])
        return "".join(pieces)
