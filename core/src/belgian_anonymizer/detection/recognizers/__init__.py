from belgian_anonymizer.detection.recognizers.base_recognizer import (
    BaseRecognizer,
    EntityPriority,
    PatternRecognizer,
)
from belgian_anonymizer.detection.recognizers.contact_recognizers import (
    BelgianPhoneRecognizer,
    EmailRecognizer,
    InternationalPhoneRecognizer,
)
from belgian_anonymizer.detection.recognizers.contextual_recognizers import (
    DateOfBirthRecognizer,
    LicensePlateRecognizer,
    StreetAddressRecognizer,
)
from belgian_anonymizer.detection.recognizers.identifier_recognizers import (
    EnterpriseNumberRecognizer,
    IbanRecognizer,
    IdCardNumberRecognizer,
    NationalNumberRecognizer,
)


def default_pattern_recognizers() -> list[BaseRecognizer]:
    return [
        NationalNumberRecognizer(),
        EnterpriseNumberRecognizer(),
        IbanRecognizer(),
        IdCardNumberRecognizer(),
        EmailRecognizer(),
        BelgianPhoneRecognizer(),
        InternationalPhoneRecognizer(),
        DateOfBirthRecognizer(),
        LicensePlateRecognizer(),
        StreetAddressRecognizer(),
    ]


__all__ = [
    "BaseRecognizer",
    "BelgianPhoneRecognizer",
    "DateOfBirthRecognizer",
    "EmailRecognizer",
    "EnterpriseNumberRecognizer",
    "EntityPriority",
    "IbanRecognizer",
    "IdCardNumberRecognizer",
    "InternationalPhoneRecognizer",
    "LicensePlateRecognizer",
    "NationalNumberRecognizer",
    "PatternRecognizer",
    "StreetAddressRecognizer",
    "default_pattern_recognizers",
]
