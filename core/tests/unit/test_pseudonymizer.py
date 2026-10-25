from belgian_anonymizer.anonymization import Pseudonymizer
from belgian_anonymizer.models.entity import DetectedEntity, EntityType


def at(
    text: str, value: str, entity_type: EntityType, occurrence: int = 0, canonical: str | None = None
) -> DetectedEntity:
    start = -1
    for _ in range(occurrence + 1):
        start = text.index(value, start + 1)
    return DetectedEntity(
        entity_type, start, start + len(value), value, 0.9, "test", canonical_text=canonical
    )


class TestPseudonymizer:
    def test_same_value_gets_same_placeholder(self) -> None:
        text = "Jan Peeters loue à Sophie Dubois. PEETERS paie. Peeters signe."
        entities = [
            at(text, "Jan Peeters", EntityType.PERSON),
            at(text, "Sophie Dubois", EntityType.PERSON),
            at(text, "PEETERS", EntityType.PERSON, canonical="Jan Peeters"),
            at(text, "Peeters", EntityType.PERSON, occurrence=1, canonical="Jan Peeters"),
        ]
        anonymized, items, mapping = Pseudonymizer().anonymize(text, entities)

        assert anonymized == "[PERSON_1] loue à [PERSON_2]. [PERSON_1] paie. [PERSON_1] signe."
        assert [item.placeholder for item in items] == [
            "[PERSON_1]",
            "[PERSON_2]",
            "[PERSON_1]",
            "[PERSON_1]",
        ]
        entry = mapping.get("[PERSON_1]")
        assert entry is not None
        assert entry.value == "Jan Peeters"
        assert entry.variants == ["Jan Peeters", "PEETERS", "Peeters"]

    def test_identifiers_are_normalised(self) -> None:
        text = "IBAN BE68 5390 0754 7034 ou BE68539007547034"
        entities = [
            at(text, "BE68 5390 0754 7034", EntityType.IBAN),
            at(text, "BE68539007547034", EntityType.IBAN),
        ]
        anonymized, _, _ = Pseudonymizer().anonymize(text, entities)
        assert anonymized == "IBAN [IBAN_1] ou [IBAN_1]"

    def test_mapping_restores_llm_answer(self) -> None:
        text = "Jan Peeters, IBAN BE68 5390 0754 7034"
        entities = [
            at(text, "Jan Peeters", EntityType.PERSON),
            at(text, "BE68 5390 0754 7034", EntityType.IBAN),
        ]
        _, _, mapping = Pseudonymizer().anonymize(text, entities)

        restored, replaced, unknown = mapping.restore("[PERSON_1] doit payer sur [IBAN_1], pas [PERSON_9].")
        assert restored == "Jan Peeters doit payer sur BE68 5390 0754 7034, pas [PERSON_9]."
        assert replaced == 2
        assert unknown == ["[PERSON_9]"]
