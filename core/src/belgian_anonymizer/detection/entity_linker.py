import re
from dataclasses import replace

from belgian_anonymizer.models.entity import DetectedEntity, EntityType

_LINKED_TYPES = {EntityType.PERSON, EntityType.ORGANIZATION}
_INITIAL = re.compile(r"[^\W\d_]\.")


class EntityLinker:
    """Links short forms detected on their own ("Peeters", "P. Peeters") to the full form ("Jan Peeters").

    Both then share one placeholder, so the LLM sees a single party. A short form matching several
    full forms (two people named Peeters) is ambiguous and keeps its own placeholder.
    """

    def link(self, entities: list[DetectedEntity]) -> list[DetectedEntity]:
        # Full forms per type, keyed case-insensitively ("Jan Peeters" = "JAN PEETERS"): (first text, words)
        full_forms: dict[EntityType, dict[str, tuple[str, frozenset[str]]]] = {
            kind: {} for kind in _LINKED_TYPES
        }
        for entity in entities:
            if entity.entity_type in _LINKED_TYPES and entity.canonical_text is None:
                text = " ".join(entity.text.split())
                full_forms[entity.entity_type].setdefault(text.casefold(), (text, self._full_words(text)))

        linked: list[DetectedEntity] = []
        for entity in entities:
            if entity.entity_type in _LINKED_TYPES and entity.canonical_text is None:
                own_key = " ".join(entity.text.split()).casefold()
                owners = [
                    text
                    for key, (text, form_words) in full_forms[entity.entity_type].items()
                    if key != own_key and self._is_short_form(entity.text, form_words)
                ]
                if len(owners) == 1:
                    entity = replace(entity, canonical_text=owners[0])
            linked.append(entity)
        return linked

    @classmethod
    def _is_short_form(cls, value: str, full_words: frozenset[str]) -> bool:
        tokens = [token.strip(",") for token in value.split()]
        initials = [token[0].casefold() for token in tokens if _INITIAL.fullmatch(token)]
        words = cls._words(" ".join(token for token in tokens if not _INITIAL.fullmatch(token)))
        if not words or not words <= full_words:
            return False
        # Each initial must stand for another word of the full form ("P." for "Pieter")
        remaining = [word for word in full_words if word not in words]
        for initial in initials:
            match = next((word for word in remaining if word.startswith(initial)), None)
            if match is None:
                return False
            remaining.remove(match)
        return bool(initials) or words < full_words

    @classmethod
    def _full_words(cls, value: str) -> frozenset[str]:
        # Initials in a full form ("Jan P. Peeters") do not count as words
        return cls._words(
            " ".join(token for token in value.split() if not _INITIAL.fullmatch(token.strip(",")))
        )

    @staticmethod
    def _words(value: str) -> frozenset[str]:
        return frozenset(word.strip(",.").casefold() for word in value.split())
