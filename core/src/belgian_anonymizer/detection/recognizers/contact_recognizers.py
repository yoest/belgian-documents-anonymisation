import re

from belgian_anonymizer.detection.recognizers.base_recognizer import EntityPriority, PatternRecognizer
from belgian_anonymizer.detection.validators import BelgianChecksumValidator
from belgian_anonymizer.models.entity import EntityType

_PHONE_SEP = r"[ ./\-]?"


class EmailRecognizer(PatternRecognizer):
    entity_type = EntityType.EMAIL
    priority = EntityPriority.FORMAT
    score = 0.99
    patterns = (re.compile(r"(?<![\w.+-])[\w.+-]+@[\w-]+(?:\.[\w-]+)*\.[A-Za-z]{2,}(?![\w-])"),)


class BelgianPhoneRecognizer(PatternRecognizer):
    """Belgian landline (02 512 34 56) and mobile (0470 12 34 56, +32 470 12 34 56) numbers."""

    entity_type = EntityType.PHONE
    priority = EntityPriority.FORMAT
    score = 0.9
    patterns = (
        re.compile(
            rf"(?<![\w+])(?:(?:\+|00)32{_PHONE_SEP}(?:\(0\)[ ]?)?|0)[1-9](?:{_PHONE_SEP}\d){{7,8}}(?![\d])"
        ),
    )

    def validate(self, value: str) -> bool:
        digits = BelgianChecksumValidator.digits(value)
        for prefix in ("0032", "320", "32", "0"):
            if digits.startswith(prefix) and (prefix != "32" or value.lstrip().startswith("+")):
                national = digits[len(prefix) :]
                break
        else:
            return False
        # Mobile numbers have 9 significant digits starting with 4, landlines have 8
        return len(national) == 8 or (len(national) == 9 and national.startswith("4"))


class InternationalPhoneRecognizer(PatternRecognizer):
    """Foreign numbers in international format (+33 6 12 34 56 78)."""

    entity_type = EntityType.PHONE
    priority = EntityPriority.FORMAT
    score = 0.8
    patterns = (
        re.compile(rf"(?<![\w+])(?:\+|00)(?!32)[1-9]\d{{0,2}}(?:{_PHONE_SEP}(?:\(0\))?\d){{7,12}}(?![\d])"),
    )
