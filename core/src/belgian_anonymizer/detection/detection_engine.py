import logging

from belgian_anonymizer.config import DetectionConfig
from belgian_anonymizer.detection.entity_filter import EntityFilter
from belgian_anonymizer.detection.entity_linker import EntityLinker
from belgian_anonymizer.detection.entity_merger import EntityMerger
from belgian_anonymizer.detection.entity_propagator import EntityPropagator
from belgian_anonymizer.detection.recognizers import BaseRecognizer, default_pattern_recognizers
from belgian_anonymizer.models.entity import DetectedEntity, EntityType

logger = logging.getLogger(__name__)


class DetectionEngine:
    """Runs every recognizer, then cleans, merges, propagates and links the detections."""

    def __init__(
        self,
        recognizers: list[BaseRecognizer],
        entity_filter: EntityFilter,
        merger: EntityMerger,
        propagator: EntityPropagator,
        linker: EntityLinker,
        enabled_types: set[EntityType],
    ) -> None:
        self._recognizers = recognizers
        self._filter = entity_filter
        self._merger = merger
        self._propagator = propagator
        self._linker = linker
        self._enabled_types = enabled_types

    @classmethod
    def from_config(cls, config: DetectionConfig) -> "DetectionEngine":
        enabled_types = set(config.enabled_entity_types)
        recognizers = default_pattern_recognizers()
        if config.ner.enabled:
            # Imported here so that the pattern-only mode does not depend on torch at all
            from belgian_anonymizer.detection.ner import GlinerRecognizer

            recognizers.append(GlinerRecognizer(config.ner, enabled_types))
        return cls(
            recognizers=recognizers,
            entity_filter=EntityFilter(config.contract_role_terms, config.person_titles),
            merger=EntityMerger(),
            propagator=EntityPropagator(
                config.propagation,
                config.name_particles,
                config.organization_legal_forms,
                config.contract_role_terms,
            ),
            linker=EntityLinker(),
            enabled_types=enabled_types,
        )

    @property
    def enabled_types(self) -> set[EntityType]:
        return set(self._enabled_types)

    def detect(self, text: str) -> list[DetectedEntity]:
        candidates: list[DetectedEntity] = []
        for recognizer in self._recognizers:
            found = [
                entity for entity in recognizer.recognize(text) if entity.entity_type in self._enabled_types
            ]
            logger.debug("%s found %d candidates", recognizer.name, len(found))
            candidates.extend(found)
        merged = self._merger.merge(text, self._filter.apply(text, candidates))
        propagated = self._filter.apply(text, self._propagator.propagate(text, merged))
        return self._linker.link(self._merger.merge(text, merged + propagated))
