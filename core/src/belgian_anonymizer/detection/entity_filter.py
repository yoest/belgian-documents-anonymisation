import re

from belgian_anonymizer.models.entity import DetectedEntity, EntityType

_EDGE_CHARS = " \t\n,;:.!?()[]{}\"'«»“”‘’-–|#*"
_LEADING_ARTICLE = re.compile(r"^(?:le|la|les|l'|l’|de|het|the|die|der|das|den|dem|des|du)\s*", re.IGNORECASE)
_NAMED_TYPES = {EntityType.PERSON, EntityType.ORGANIZATION}
_TEXTUAL_TYPES = _NAMED_TYPES | {EntityType.ADDRESS}


class EntityFilter:
    """Cleans NER spans: trims punctuation, strips titles ("Monsieur"), drops contract roles ("le Bailleur").

    Titles and roles carry meaning for the LLM but do not identify anyone, so they stay in clear text.
    """

    def __init__(self, contract_role_terms: list[str], person_titles: list[str]) -> None:
        self._role_terms = {term.casefold() for term in contract_role_terms}
        titles = "|".join(re.escape(title) for title in sorted(person_titles, key=len, reverse=True))
        self._title_pattern = re.compile(rf"(?:{titles})\.?\s+", re.IGNORECASE) if titles else None

    def apply(self, text: str, entities: list[DetectedEntity]) -> list[DetectedEntity]:
        cleaned = (self._clean(text, entity) for entity in entities)
        return [entity for entity in cleaned if entity is not None]

    def _clean(self, text: str, entity: DetectedEntity) -> DetectedEntity | None:
        start, end = entity.start, entity.end
        if entity.entity_type in _TEXTUAL_TYPES:
            start, end = self._trim(text, start, end)
        if entity.entity_type is EntityType.PERSON and self._title_pattern:
            while match := self._title_pattern.match(text, start, end):
                start = match.end()
        value = text[start:end]
        if entity.entity_type in _TEXTUAL_TYPES and (len(value) < 2 or not any(c.isupper() for c in value)):
            return None
        if entity.entity_type in _NAMED_TYPES and self._is_role_term(value):
            return None
        return entity.with_span(start, end, value)

    @staticmethod
    def _trim(text: str, start: int, end: int) -> tuple[int, int]:
        while start < end and text[start] in _EDGE_CHARS:
            start += 1
        while end > start and text[end - 1] in _EDGE_CHARS:
            # Keep a closing parenthesis that belongs to the value, e.g. "Immo SRL (Liège)"
            if text[end - 1] == ")" and "(" in text[start : end - 1]:
                break
            end -= 1
        return start, end

    def _is_role_term(self, value: str) -> bool:
        normalized = " ".join(_LEADING_ARTICLE.sub("", value).split()).casefold()
        return normalized in self._role_terms
