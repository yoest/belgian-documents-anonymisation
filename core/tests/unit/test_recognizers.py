import pytest

from belgian_anonymizer.detection.recognizers import (
    BelgianPhoneRecognizer,
    DateOfBirthRecognizer,
    EmailRecognizer,
    EnterpriseNumberRecognizer,
    IbanRecognizer,
    IdCardNumberRecognizer,
    InternationalPhoneRecognizer,
    LicensePlateRecognizer,
    NationalNumberRecognizer,
    PatternRecognizer,
    StreetAddressRecognizer,
)
from belgian_anonymizer.models.entity import EntityType
from tests.fixtures.contract_factory import SyntheticIdentifiers

NISS = SyntheticIdentifiers.national_number("850730", "033")
ENTERPRISE = SyntheticIdentifiers.enterprise_number("07123456")
IBAN = SyntheticIdentifiers.belgian_iban("3630123456")
ID_CARD = SyntheticIdentifiers.id_card_number("5921234567")


def found(recognizer: PatternRecognizer, text: str) -> list[str]:
    return [entity.text for entity in recognizer.recognize(text)]


class TestIdentifiers:
    @pytest.mark.parametrize(
        "formatted", [NISS, NISS.replace(".", "").replace("-", ""), NISS.replace(".", " ")]
    )
    def test_national_number_formats(self, formatted: str) -> None:
        assert found(NationalNumberRecognizer(), f"registre national {formatted}, domicilié") == [formatted]

    def test_national_number_rejects_invalid_checksum(self) -> None:
        assert found(NationalNumberRecognizer(), "référence 85.07.30-033.00") == []

    def test_enterprise_number_with_and_without_prefix(self) -> None:
        bare = ENTERPRISE.removeprefix("BE ")
        assert found(EnterpriseNumberRecognizer(), f"TVA {ENTERPRISE} ou BCE {bare}.") == [ENTERPRISE, bare]

    def test_iban_does_not_swallow_following_word(self) -> None:
        assert found(IbanRecognizer(), f"compte {IBAN} BIC GEBABEBB") == [IBAN]

    def test_iban_rejects_invalid_checksum(self) -> None:
        assert found(IbanRecognizer(), "compte BE00 3630 1234 5600") == []

    def test_id_card_number(self) -> None:
        entities = IdCardNumberRecognizer().recognize(f"carte d'identité n° {ID_CARD}")
        assert [(e.text, e.entity_type) for e in entities] == [(ID_CARD, EntityType.ID_CARD_NUMBER)]

    def test_old_bank_account_format_is_labelled_iban(self) -> None:
        entities = IdCardNumberRecognizer().recognize(f"sur le compte bancaire {ID_CARD}")
        assert [e.entity_type for e in entities] == [EntityType.IBAN]


class TestContact:
    @pytest.mark.parametrize(
        "phone",
        ["+32 470 12 34 56", "0470/12.34.56", "02 512 34 56", "0032 2 512 34 56", "+32 (0)9 123 45 67"],
    )
    def test_belgian_phones(self, phone: str) -> None:
        assert found(BelgianPhoneRecognizer(), f"tél. {phone}.") == [phone]

    @pytest.mark.parametrize("text", ["le 01/02/2024", "montant de 1.250.000 euros", "article 0123"])
    def test_belgian_phone_ignores_dates_and_amounts(self, text: str) -> None:
        assert found(BelgianPhoneRecognizer(), text) == []

    def test_international_phone(self) -> None:
        assert found(InternationalPhoneRecognizer(), "portable +33 6 12 34 56 78") == ["+33 6 12 34 56 78"]

    def test_email(self) -> None:
        assert found(EmailRecognizer(), "contact: jan.peeters+bail@example.be.") == [
            "jan.peeters+bail@example.be"
        ]


class TestContextual:
    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("né le 30/07/1985 à Louvain", "30/07/1985"),
            ("née à Liège, le 3 mars 1990", "3 mars 1990"),
            ("geboren te Gent op 15/03/2002", "15/03/2002"),
            ("Geboortedatum: 1 januari 1970", "1 januari 1970"),
            ("geboren am 12.05.1970 in Eupen", "12.05.1970"),
            ("geboren in Eupen am 3. August 1988", "3. August 1988"),
        ],
    )
    def test_date_of_birth(self, text: str, expected: str) -> None:
        assert found(DateOfBirthRecognizer(), text) == [expected]

    def test_other_dates_are_kept(self) -> None:
        assert found(DateOfBirthRecognizer(), "Fait à Bruxelles, le 1er septembre 2025") == []

    @pytest.mark.parametrize("plate", ["1-ABC-123", "ABC-123"])
    def test_license_plate(self, plate: str) -> None:
        assert found(LicensePlateRecognizer(), f"véhicule {plate}.") == [plate]

    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("domicilié Rue de la Loi 16, 1000 Bruxelles, téléphone", "Rue de la Loi 16, 1000 Bruxelles"),
            ("situé avenue Louise 54 bte 3 à Ixelles", "avenue Louise 54 bte 3"),
            ("wonende te Kerkstraat 5 bus 2, 9000 Gent, telefoon", "Kerkstraat 5 bus 2, 9000 Gent"),
        ],
    )
    def test_street_address(self, text: str, expected: str) -> None:
        assert found(StreetAddressRecognizer(), text) == [expected]

    def test_street_keyword_in_normal_sentence_is_ignored(self) -> None:
        assert (
            found(StreetAddressRecognizer(), "un emplacement de parking n° 3 est mis en place 2 fois") == []
        )
