import re
from dataclasses import dataclass

from belgian_anonymizer.config import PropagationConfig
from belgian_anonymizer.detection.recognizers.base_recognizer import EntityPriority
from belgian_anonymizer.models.entity import DetectedEntity, EntityType

_PROPAGATED_TYPES = {EntityType.PERSON, EntityType.ORGANIZATION, EntityType.ADDRESS}
_SCORE_FACTOR = 0.9


@dataclass(frozen=True, slots=True)
class _SearchTerm:
    pattern: re.Pattern[str]
    source: DetectedEntity
    # Set for partial forms ("Peeters" for "Jan Peeters") so they share the placeholder of the full form
    canonical_text: str | None


class EntityPropagator:
    """Finds every other occurrence of the names detected once, as NER does not catch all of them.

    Contracts repeat party names in headers, clauses and signature blocks ("PEETERS", "M. Peeters"):
    a single missed occurrence would leak the identity.
    """

    def __init__(
        self,
        config: PropagationConfig,
        name_particles: list[str],
        organization_legal_forms: list[str],
        contract_role_terms: list[str],
    ) -> None:
        self._config = config
        self._particles = {particle.casefold() for particle in name_particles}
        self._legal_forms = {form.casefold() for form in organization_legal_forms}
        self._role_terms = {term.casefold() for term in contract_role_terms}

    def propagate(self, text: str, entities: list[DetectedEntity]) -> list[DetectedEntity]:
        if not self._config.enabled:
            return []
        propagated: list[DetectedEntity] = []
        for term in self._search_terms(entities):
            for match in term.pattern.finditer(text):
                propagated.append(
                    DetectedEntity(
                        entity_type=term.source.entity_type,
                        start=match.start(),
                        end=match.end(),
                        text=match.group(0),
                        score=term.source.score * _SCORE_FACTOR,
                        source="propagation",
                        priority=EntityPriority.PROPAGATED,
                        canonical_text=term.canonical_text,
                    )
                )
        return propagated

    def _search_terms(self, entities: list[DetectedEntity]) -> list[_SearchTerm]:
        terms: dict[str, _SearchTerm] = {}
        for entity in entities:
            if entity.entity_type not in _PROPAGATED_TYPES or len(entity.text) < 3:
                continue
            key = f"{entity.entity_type}:{entity.text.casefold()}"
            terms.setdefault(key, _SearchTerm(self._full_form_pattern(entity.text), entity, None))
            canonical = entity.canonical_text or entity.text
            for part_key, pattern in self._partial_forms(entity):
                terms.setdefault(f"{entity.entity_type}:{part_key}", _SearchTerm(pattern, entity, canonical))
        return list(terms.values())

    @staticmethod
    def _full_form_pattern(value: str) -> re.Pattern[str]:
        words = [re.escape(word) for word in value.split()]
        return re.compile(rf"(?<!\w){r'\s+'.join(words)}(?!\w)", re.IGNORECASE)

    def _partial_forms(self, entity: DetectedEntity) -> list[tuple[str, re.Pattern[str]]]:
        if entity.entity_type is EntityType.PERSON and self._config.propagate_name_parts:
            return self._name_parts(entity.text)
        if entity.entity_type is EntityType.ORGANIZATION:
            return self._organization_core_name(entity.text)
        return []

    def _name_parts(self, name: str) -> list[tuple[str, re.Pattern[str]]]:
        words = name.split()
        if len(words) < 2:
            return []
        parts: list[tuple[str, re.Pattern[str]]] = []
        for index, word in enumerate(words):
            core = word.strip(",.")
            is_initial = word.endswith(".") or len(core) < self._config.min_name_part_length
            if is_initial or not core[0].isupper() or core.casefold() in self._particles | self._role_terms:
                continue
            # Particles written before the part in the full name are optional ("Van Den Berg" -> "Berg")
            particles: list[str] = []
            for previous in reversed(words[:index]):
                if previous.casefold() not in self._particles:
                    break
                particles.insert(0, re.escape(previous))
            prefix = rf"(?:(?i:{r'\s+'.join(particles)})\s+)?" if particles else ""
            # Case-sensitive (as written or uppercase) so that the name "Roi" does not match "roi"
            variants = "|".join(dict.fromkeys((re.escape(core), re.escape(core.upper()))))
            parts.append((core.casefold(), re.compile(rf"(?<!\w){prefix}(?:{variants})(?!\w)")))
        return parts

    def _organization_core_name(self, name: str) -> list[tuple[str, re.Pattern[str]]]:
        words = name.split()
        while words and words[-1].strip(",.").casefold() in self._legal_forms:
            words.pop()
        while words and words[0].strip(",.").casefold() in self._legal_forms:
            words.pop(0)
        core = " ".join(words)
        if core == name or len(core) < 4 or core.casefold() in self._role_terms:
            return []
        return [(core.casefold(), self._full_form_pattern(core))]
