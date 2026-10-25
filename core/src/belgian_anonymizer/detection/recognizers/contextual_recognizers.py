import re

from belgian_anonymizer.detection.recognizers.base_recognizer import EntityPriority, PatternRecognizer
from belgian_anonymizer.models.entity import EntityType

_MONTHS = (
    "janvier|février|fevrier|mars|avril|mai|juin|juillet|août|aout|septembre|octobre|novembre|décembre|decembre"
    "|januari|februari|maart|april|mei|juni|juli|augustus|oktober"
    "|january|february|march|may|june|july|august|september|october|november|december"
    "|januar|februar|märz|maerz|dezember"
)
_DATE = rf"(?:\d{{1,2}}[./\-]\d{{1,2}}[./\-]\d{{2,4}}|\d{{1,2}}(?:er|e|\.)?\s+(?:{_MONTHS})\s+\d{{4}})"
# Place of birth may sit between the keyword and the date: "né à Liège le 30 juillet 1985"
_PLACE = r"(?:\s+(?:à|a|te|in)\s+[^\n,;]{1,40}?,?)?"


class DateOfBirthRecognizer(PatternRecognizer):
    """Dates preceded by a birth keyword; other contract dates (signature, term) are kept."""

    entity_type = EntityType.DATE_OF_BIRTH
    priority = EntityPriority.CONTEXTUAL
    score = 0.95
    patterns = (
        re.compile(
            rf"(?:\bnée?{_PLACE}\s+le|\bgeboren{_PLACE}\s+(?:op|am)|\bborn{_PLACE}\s+on"
            rf"|date\s+de\s+naissance|geboortedatum|geburtsdatum|date\s+of\s+birth)\s*:?\s*(?P<value>{_DATE})",
            re.IGNORECASE,
        ),
    )


class LicensePlateRecognizer(PatternRecognizer):
    """Belgian plates: current 1-ABC-123 and older ABC-123 formats."""

    entity_type = EntityType.LICENSE_PLATE
    priority = EntityPriority.FORMAT
    score = 0.85
    patterns = (re.compile(r"(?<![\w\-])(?:[1-9]-)?[A-Z]{3}-\d{3}(?![\w\-])"),)


class StreetAddressRecognizer(PatternRecognizer):
    """Street + number (+ box, postal code, municipality); complements the NER address detection."""

    entity_type = EntityType.ADDRESS
    priority = EntityPriority.CONTEXTUAL
    score = 0.8
    _NUMBER = r"\d{1,4}(?:[ ]?[A-Za-z](?!\w))?(?:[ ,/]*(?:bte|boîte|bt|bus|b)\.?[ ]?\w{1,4})?"
    _POSTAL = r"(?:[ ]*[,\-]?[ ]*(?:B-)?[1-9]\d{3}[ ]+[A-ZÀ-Ý][\w'\-]+(?:[ \-][A-ZÀ-Ý(][\w'\-)]+)*)?"
    patterns = (
        # The word right before the number must be capitalised, to skip "place de parking 3"
        re.compile(
            r"(?<!\w)(?i:rue|avenue|av\.|boulevard|bd|chaussée|place|square|quai|clos|allée|impasse|chemin"
            r"|drève|route|sentier|rond-point|cité|galerie)"
            rf"[ ]+(?:[\w'\-]+[ ]+){{0,5}}?[A-ZÀ-Ý][\w'\-]*[ ,]+{_NUMBER}{_POSTAL}"
        ),
        # Dutch street types are suffixes ("Kerkstraat") or separate words after a name ("Grote Markt")
        re.compile(
            r"(?<!\w)(?:[A-ZÀ-Ý][\w'\-]*(?:straat|laan|steenweg|plein|weg|dreef|lei|kaai|baan|dijk|markt|pad"
            r"|singel|hof|park|vest|wal)|(?:[A-ZÀ-Ý][\w'\-]*[ ]+){1,2}(?:Straat|Laan|Steenweg|Plein|Markt"
            rf"|Kaai|Dreef|Lei|Vest|Wal))[ ,]+{_NUMBER}{_POSTAL}"
        ),
    )
