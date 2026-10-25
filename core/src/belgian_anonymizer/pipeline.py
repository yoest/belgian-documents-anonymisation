import logging
import time
from collections import Counter

from belgian_anonymizer.anonymization import Pseudonymizer
from belgian_anonymizer.config import AppConfig
from belgian_anonymizer.detection import DetectionEngine
from belgian_anonymizer.extraction import PdfExtractor
from belgian_anonymizer.models.entity import EntityType
from belgian_anonymizer.models.result import AnonymizationResult

logger = logging.getLogger(__name__)


class AnonymizationPipeline:
    """PDF bytes -> Markdown (Docling) -> detected entities -> anonymised Markdown + mapping."""

    def __init__(
        self,
        extractor: PdfExtractor,
        detection_engine: DetectionEngine,
        pseudonymizer: Pseudonymizer,
    ) -> None:
        self._extractor = extractor
        self._detection_engine = detection_engine
        self._pseudonymizer = pseudonymizer

    @classmethod
    def from_config(cls, config: AppConfig) -> "AnonymizationPipeline":
        return cls(
            extractor=PdfExtractor(config.extraction),
            detection_engine=DetectionEngine.from_config(config.detection),
            pseudonymizer=Pseudonymizer(),
        )

    def warm_up(self) -> None:
        self._extractor.warm_up()

    @property
    def enabled_types(self) -> set[EntityType]:
        return self._detection_engine.enabled_types

    def run(self, content: bytes, filename: str) -> AnonymizationResult:
        started = time.perf_counter()
        document = self._extractor.extract(content, filename)
        entities = self._detection_engine.detect(document.text)
        anonymized_text, anonymized, mapping = self._pseudonymizer.anonymize(document.text, entities)
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        # Only counts are logged: document content must never end up in logs
        logger.info(
            "Anonymised %d page(s) in %d ms: %s",
            document.page_count,
            elapsed_ms,
            dict(Counter(str(item.entity.entity_type) for item in anonymized)),
        )
        return AnonymizationResult(document, anonymized_text, anonymized, mapping, elapsed_ms)
