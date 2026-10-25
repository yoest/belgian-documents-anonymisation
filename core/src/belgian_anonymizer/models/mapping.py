import re
from dataclasses import dataclass, field

from belgian_anonymizer.models.entity import EntityType

PLACEHOLDER_PATTERN = re.compile(r"\[(?P<key>[A-Z][A-Z_]*_\d+)\]")


@dataclass(slots=True)
class MappingEntry:
    placeholder: str
    entity_type: EntityType
    # Value restored on de-anonymisation (the most complete form, e.g. "Jan Peeters")
    value: str
    # Every surface form found in the document for this placeholder ("Jan Peeters", "PEETERS", ...)
    variants: list[str] = field(default_factory=list)

    def add_variant(self, variant: str) -> None:
        if variant not in self.variants:
            self.variants.append(variant)


class AnonymizationMapping:
    """Placeholder -> original value table, which must never be sent to the LLM."""

    def __init__(self, entries: list[MappingEntry] | None = None) -> None:
        self._entries: dict[str, MappingEntry] = {entry.placeholder: entry for entry in entries or []}

    @property
    def entries(self) -> list[MappingEntry]:
        return list(self._entries.values())

    def get(self, placeholder: str) -> MappingEntry | None:
        return self._entries.get(placeholder)

    def add(self, entry: MappingEntry) -> None:
        self._entries[entry.placeholder] = entry

    def restore(self, text: str) -> tuple[str, int, list[str]]:
        """Replace known placeholders by their original value.

        Returns the restored text, the number of replacements and the unknown placeholders
        (e.g. hallucinated by the LLM), which are left untouched.
        """
        replaced = 0
        unknown: list[str] = []

        def substitute(match: re.Match[str]) -> str:
            nonlocal replaced
            entry = self._entries.get(match.group(0))
            if entry is None:
                if match.group(0) not in unknown:
                    unknown.append(match.group(0))
                return match.group(0)
            replaced += 1
            return entry.value

        return PLACEHOLDER_PATTERN.sub(substitute, text), replaced, unknown
