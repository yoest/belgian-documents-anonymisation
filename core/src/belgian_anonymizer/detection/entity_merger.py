from dataclasses import replace

from belgian_anonymizer.models.entity import DetectedEntity


class EntityMerger:
    """Resolves overlapping detections into a sorted list of non-overlapping entities.

    Candidates are accepted by priority, then length, then score. An overlap with an accepted entity
    of the same type extends it (union of both spans, so nothing leaks at the edges); an overlap
    with another type is dropped.
    """

    def merge(self, text: str, entities: list[DetectedEntity]) -> list[DetectedEntity]:
        accepted: list[DetectedEntity] = []
        for candidate in sorted(entities, key=lambda e: (-e.priority, -e.length, -e.score, e.start)):
            overlapping = [entity for entity in accepted if entity.overlaps(candidate)]
            if not overlapping:
                accepted.append(candidate)
            elif all(entity.entity_type is candidate.entity_type for entity in overlapping):
                for entity in overlapping:
                    accepted.remove(entity)
                accepted.append(self._union(text, [*overlapping, candidate]))
        return sorted(accepted, key=lambda e: e.start)

    @staticmethod
    def _union(text: str, entities: list[DetectedEntity]) -> DetectedEntity:
        # The highest-priority entity keeps its metadata, only the span grows
        best = max(entities, key=lambda e: (e.priority, e.score))
        start = min(entity.start for entity in entities)
        end = max(entity.end for entity in entities)
        return replace(best, start=start, end=end, text=text[start:end], score=max(e.score for e in entities))
