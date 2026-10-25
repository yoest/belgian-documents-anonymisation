import pytest

from belgian_anonymizer.detection.validators import BelgianChecksumValidator
from tests.fixtures.contract_factory import SyntheticIdentifiers


class TestNationalNumber:
    def test_accepts_valid_number_born_before_2000(self) -> None:
        assert BelgianChecksumValidator.is_valid_national_number(
            SyntheticIdentifiers.national_number("850730", "033")
        )

    def test_accepts_valid_number_born_after_2000(self) -> None:
        number = SyntheticIdentifiers.national_number("020315", "122", born_after_2000=True)
        assert BelgianChecksumValidator.is_valid_national_number(number)

    def test_accepts_bis_number(self) -> None:
        # BIS numbers add 20 or 40 to the birth month
        assert BelgianChecksumValidator.is_valid_national_number(
            SyntheticIdentifiers.national_number("854730", "033")
        )

    def test_rejects_wrong_check_digits(self) -> None:
        number = SyntheticIdentifiers.national_number("850730", "033")
        wrong = number[:-2] + f"{(int(number[-2:]) + 1) % 100:02d}"
        assert not BelgianChecksumValidator.is_valid_national_number(wrong)

    def test_rejects_impossible_month(self) -> None:
        assert not BelgianChecksumValidator.is_valid_national_number("85.15.30-033.00")


class TestEnterpriseNumber:
    def test_accepts_valid_number(self) -> None:
        number = SyntheticIdentifiers.enterprise_number("07123456")
        assert BelgianChecksumValidator.is_valid_enterprise_number(number)

    @pytest.mark.parametrize("value", ["0712.345.600", "2712.345.645", "071234"])
    def test_rejects_invalid_numbers(self, value: str) -> None:
        assert not BelgianChecksumValidator.is_valid_enterprise_number(value)


class TestIban:
    def test_accepts_belgian_iban(self) -> None:
        assert BelgianChecksumValidator.is_valid_iban(SyntheticIdentifiers.belgian_iban("3630123456"))

    def test_accepts_foreign_iban(self) -> None:
        # Standard example IBAN from the ISO 13616 documentation
        assert BelgianChecksumValidator.is_valid_iban("FR14 2004 1010 0505 0001 3M02 606")

    def test_rejects_altered_iban(self) -> None:
        iban = SyntheticIdentifiers.belgian_iban("3630123456")
        assert not BelgianChecksumValidator.is_valid_iban(iban[:-1] + str((int(iban[-1]) + 1) % 10))


class TestMod97Remainder:
    def test_accepts_id_card_number(self) -> None:
        number = SyntheticIdentifiers.id_card_number("5921234567")
        assert BelgianChecksumValidator.is_valid_mod97_remainder(number)

    def test_remainder_zero_is_written_97(self) -> None:
        assert BelgianChecksumValidator.is_valid_mod97_remainder("000000009797")
