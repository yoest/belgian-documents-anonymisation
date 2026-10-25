import re

_NON_DIGIT = re.compile(r"\D")
_NON_ALNUM = re.compile(r"[^0-9A-Za-z]")


class BelgianChecksumValidator:
    """Modulo-97 checks used by Belgian identifiers, to reject random digit sequences."""

    @staticmethod
    def digits(value: str) -> str:
        return _NON_DIGIT.sub("", value)

    @staticmethod
    def mod97_complement(number: int) -> int:
        # Check digits defined as 97 - (n mod 97), which yields 97 instead of 0
        return 97 - number % 97

    @classmethod
    def is_valid_national_number(cls, value: str) -> bool:
        """National register (NISS/INSZ) or BIS number: YYMMDD SSS CC."""
        digits = cls.digits(value)
        if len(digits) != 11:
            return False
        month, day = int(digits[2:4]), int(digits[4:6])
        # BIS numbers shift the month by +20 (unknown gender) or +40 (known gender); 00 = unknown date
        if month % 20 > 12 or month > 52 or day > 31:
            return False
        base, check = digits[:9], int(digits[9:])
        # People born from 2000 onwards get a "2" prepended before computing the checksum
        return check in (cls.mod97_complement(int(base)), cls.mod97_complement(int("2" + base)))

    @classmethod
    def is_valid_enterprise_number(cls, value: str) -> bool:
        """Crossroads Bank for Enterprises (KBO/BCE) number, also the VAT number: 0XXX.XXX.XXX."""
        digits = cls.digits(value)
        if len(digits) != 10 or digits[0] not in "01":
            return False
        return int(digits[8:]) == cls.mod97_complement(int(digits[:8]))

    @classmethod
    def is_valid_mod97_remainder(cls, value: str) -> bool:
        """Old bank account and eID card numbers: 12 digits, last two = first ten mod 97 (97 if 0)."""
        digits = cls.digits(value)
        if len(digits) != 12:
            return False
        remainder = int(digits[:10]) % 97
        return int(digits[10:]) == (remainder or 97)

    @classmethod
    def is_valid_iban(cls, value: str) -> bool:
        """ISO 13616 IBAN check, plus the national bank account check for Belgian IBANs."""
        iban = _NON_ALNUM.sub("", value).upper()
        if not 15 <= len(iban) <= 34 or not iban[:2].isalpha() or not iban[2:4].isdigit():
            return False
        if iban.startswith("BE") and (len(iban) != 16 or not cls.is_valid_mod97_remainder(iban[4:])):
            return False
        rearranged = iban[4:] + iban[:4]
        numeric = "".join(str(int(char, 36)) for char in rearranged)
        return int(numeric) % 97 == 1
