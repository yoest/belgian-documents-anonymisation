import logging
import threading
from typing import Any

from belgian_anonymizer.config import NerConfig
from belgian_anonymizer.cpu import physical_core_estimate
from belgian_anonymizer.detection.ner.text_chunker import TextChunker
from belgian_anonymizer.detection.recognizers.base_recognizer import BaseRecognizer, EntityPriority
from belgian_anonymizer.models.entity import DetectedEntity, EntityType

logger = logging.getLogger(__name__)


class GlinerRecognizer(BaseRecognizer):
    """Multilingual (FR/NL/DE/EN) zero-shot NER for names, organisations and addresses."""

    def __init__(self, config: NerConfig, enabled_types: set[EntityType]) -> None:
        # Imported lazily: torch takes seconds to import and is not needed when NER is disabled
        import torch
        from gliner import GLiNER

        self._disable_runtime_telemetry()
        torch.set_num_threads(config.torch_threads or physical_core_estimate())
        self._labels = {label: kind for label, kind in config.labels.items() if kind in enabled_types}
        self._threshold = config.threshold
        self._chunker = TextChunker(config.chunk_size_words, config.chunk_overlap_words)
        # The model is not designed for concurrent calls and already uses every allotted CPU thread
        self._lock = threading.Lock()
        logger.info("Loading NER model %s", config.model_name)
        self._model: Any = GLiNER.from_pretrained(config.model_name)
        self._model.inference(["Warm-up de Jan Peeters à Bruxelles."], list(self._labels) or ["person"])

    @staticmethod
    def _disable_runtime_telemetry() -> None:
        # Documents are confidential: if an optional ONNX runtime is installed, it must not report usage
        try:
            import onnxruntime
        except ImportError:
            return
        onnxruntime.disable_telemetry_events()

    def recognize(self, text: str) -> list[DetectedEntity]:
        chunks = self._chunker.split(text)
        if not chunks or not self._labels:
            return []
        with self._lock:
            predictions = self._model.inference(
                [chunk.text for chunk in chunks], list(self._labels), threshold=self._threshold
            )
        entities: list[DetectedEntity] = []
        for chunk, chunk_predictions in zip(chunks, predictions, strict=True):
            for prediction in chunk_predictions:
                start = chunk.offset + prediction["start"]
                end = chunk.offset + prediction["end"]
                entities.append(
                    DetectedEntity(
                        entity_type=self._labels[prediction["label"]],
                        start=start,
                        end=end,
                        text=text[start:end],
                        score=float(prediction["score"]),
                        source=self.name,
                        priority=EntityPriority.CONTEXTUAL,
                    )
                )
        return entities
