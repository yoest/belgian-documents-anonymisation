import re

from belgian_anonymizer.detection.recognizers.base_recognizer import EntityPriority, PatternRecognizer
from belgian_anonymizer.detection.validators import BelgianChecksumValidator
from belgian_anonymizer.models.entity import DetectedEntity, EntityType

_SEP = r"[ .\-]?"
_BANK_CONTEXT = re.compile(r"(compte|rekening|account|iban|banque|bank)", re.IGNORECASE)


class NationalNumberRecognizer(PatternRecognizer):
    """National register (NISS/INSZ/RRN) and BIS numbers, e.g. 85.07.30-033.61."""

    entity_type = EntityType.NATIONAL_NUMBER
    priority = EntityPriority.CHECKSUM
    score = 0.99
    patterns = (
        re.compile(rf"(?<![\d.])\d{{2}}{_SEP}\d{{2}}{_SEP}\d{{2}}{_SEP}\d{{3}}{_SEP}\d{{2}}(?![\d])"),
    )

    def validate(self, value: str) -> bool:
        return BelgianChecksumValidator.is_valid_national_number(value)


class EnterpriseNumberRecognizer(PatternRecognizer):
    """KBO/BCE enterprise number and VAT number, e.g. BE 0403.170.701."""

    entity_type = EntityType.ENTERPRISE_NUMBER
    priority = EntityPriority.CHECKSUM
    score = 0.99
    patterns = (
        re.compile(r"(?<![\w.])(?:BE\s?)?[01]\d{3}[ .]?\d{3}[ .]?\d{3}(?![\d])", re.IGNORECASE),
        # Without leading zero, only when explicitly prefixed (BE 403.170.701)
        re.compile(r"(?<![\w.])BE\s?[1-9]\d{2}[ .]?\d{3}[ .]?\d{3}(?![\d])", re.IGNORECASE),
    )

    def validate(self, value: str) -> bool:
        return BelgianChecksumValidator.is_valid_enterprise_number(
            BelgianChecksumValidator.digits(value).zfill(10)
        )


class IbanRecognizer(PatternRecognizer):
    """IBAN of any country, with a full checksum check (e.g. BE68 5390 0754 7034)."""

    entity_type = EntityType.IBAN
    priority = EntityPriority.CHECKSUM
    score = 0.99
    patterns = (re.compile(r"(?<![A-Za-z0-9])[A-Z]{2}\d{2}(?:[ ]?[A-Z0-9]{2,4}){3,8}(?![A-Za-z0-9])"),)

    def recognize(self, text: str) -> list[DetectedEntity]:
        entities: list[DetectedEntity] = []
        for pattern in self.patterns:
            for match in pattern.finditer(text):
                end = self._longest_valid_end(text, match.start(), match.end())
                if end is not None:
                    entities.append(
                        DetectedEntity(
                            self.entity_type,
                            match.start(),
                            end,
                            text[match.start() : end],
                            self.score,
                            self.name,
                            self.priority,
                        )
                    )
        return entities

    @staticmethod
    def _longest_valid_end(text: str, start: int, end: int) -> int | None:
        # The greedy match may swallow a following word ("BE68 5390 0754 7034 BIC"): drop groups until valid
        while end - start >= 15:
            if BelgianChecksumValidator.is_valid_iban(text[start:end]):
                return end
            last_space = text.rfind(" ", start, end)
            if last_space == -1:
                return None
            end = last_space
        return None


class IdCardNumberRecognizer(PatternRecognizer):
    """Belgian eID card number (592-1234567-89), also the format of pre-IBAN bank accounts."""

    entity_type = EntityType.ID_CARD_NUMBER
    priority = EntityPriority.CHECKSUM
    score = 0.95
    patterns = (re.compile(r"(?<![\d.\-])\d{3}[ \-]?\d{7}[ \-]?\d{2}(?![\d\-])"),)

    def validate(self, value: str) -> bool:
        return BelgianChecksumValidator.is_valid_mod97_remainder(value)

    def resolve_type(self, text: str, start: int) -> EntityType:
        # Same checksum as old account numbers: rely on nearby words to tell them apart
        if _BANK_CONTEXT.search(text[max(0, start - 50) : start]):
            return EntityType.IBAN
        return self.entity_type
