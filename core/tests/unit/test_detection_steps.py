from belgian_anonymizer.config import AppConfig, PropagationConfig
from belgian_anonymizer.detection import EntityFilter, EntityLinker, EntityMerger, EntityPropagator
from belgian_anonymizer.models.entity import DetectedEntity, EntityType


def entity(
    text: str, value: str, entity_type: EntityType = EntityType.PERSON, priority: int = 10
) -> DetectedEntity:
    start = text.index(value)
    return DetectedEntity(entity_type, start, start + len(value), value, 0.9, "test", priority)


class TestEntityFilter:
    def setup_method(self) -> None:
        detection = AppConfig.load().detection
        self.filter = EntityFilter(detection.contract_role_terms, detection.person_titles)

    def test_strips_titles_and_punctuation(self) -> None:
        text = "Entre Monsieur Jan Peeters, et De heer Pieter Janssens."
        cleaned = self.filter.apply(
            text, [entity(text, "Monsieur Jan Peeters,"), entity(text, "De heer Pieter Janssens.")]
        )
        assert [e.text for e in cleaned] == ["Jan Peeters", "Pieter Janssens"]

    def test_keeps_surname_that_looks_like_title_prefix(self) -> None:
        text = "Mehdi Benali"
        assert [e.text for e in self.filter.apply(text, [entity(text, text)])] == ["Mehdi Benali"]

    def test_drops_contract_roles(self) -> None:
        text = "ci-après « le Bailleur » et hierna de Huurder"
        candidates = [entity(text, "le Bailleur"), entity(text, "de Huurder", EntityType.ORGANIZATION)]
        assert self.filter.apply(text, candidates) == []


class TestEntityMerger:
    def test_checksum_identifier_wins_over_lower_priority(self) -> None:
        text = "tel 0712.345.678"
        phone = entity(text, "0712.345.678", EntityType.PHONE, priority=20)
        enterprise = entity(text, "0712.345.678", EntityType.ENTERPRISE_NUMBER, priority=30)
        assert [e.entity_type for e in EntityMerger().merge(text, [phone, enterprise])] == [
            EntityType.ENTERPRISE_NUMBER
        ]

    def test_same_type_overlaps_are_unioned(self) -> None:
        text = "domicilié Rue de la Loi 16, 1000 Bruxelles."
        first = entity(text, "Rue de la Loi 16", EntityType.ADDRESS)
        second = entity(text, "16, 1000 Bruxelles", EntityType.ADDRESS)
        assert [e.text for e in EntityMerger().merge(text, [first, second])] == [
            "Rue de la Loi 16, 1000 Bruxelles"
        ]


class TestEntityPropagator:
    def setup_method(self) -> None:
        detection = AppConfig.load().detection
        self.propagator = EntityPropagator(
            PropagationConfig(),
            detection.name_particles,
            detection.organization_legal_forms,
            detection.contract_role_terms,
        )

    def test_finds_full_name_parts_and_uppercase_forms(self) -> None:
        text = "Jan Peeters, ... M. Peeters ... signé JAN PEETERS ... le roi Peeterson"
        found = self.propagator.propagate(text, [entity(text, "Jan Peeters")])
        assert sorted({(e.text, e.canonical_text) for e in found}) == [
            ("JAN", "Jan Peeters"),
            ("JAN PEETERS", None),
            ("Jan", "Jan Peeters"),
            ("Jan Peeters", None),
            ("PEETERS", "Jan Peeters"),
            ("Peeters", "Jan Peeters"),
        ]

    def test_name_parts_keep_their_particles(self) -> None:
        text = "Marie De Smet ... signé M. De Smet"
        found = self.propagator.propagate(text, [entity(text, "Marie De Smet")])
        assert "De Smet" in {e.text for e in found}

    def test_organization_core_name_without_legal_form(self) -> None:
        text = "Immo Vandenberghe SRL ... adressée à Immo Vandenberghe."
        found = self.propagator.propagate(
            text, [entity(text, "Immo Vandenberghe SRL", EntityType.ORGANIZATION)]
        )
        assert ("Immo Vandenberghe", "Immo Vandenberghe SRL") in {(e.text, e.canonical_text) for e in found}


class TestEntityLinker:
    def test_short_form_takes_the_full_form_as_canonical(self) -> None:
        text = "Jan Peeters ... JAN PEETERS ... M. Peeters"
        entities = [entity(text, "Jan Peeters"), entity(text, "JAN PEETERS"), entity(text, "Peeters")]
        assert [e.canonical_text for e in EntityLinker().link(entities)] == [None, None, "Jan Peeters"]

    def test_ambiguous_short_form_is_not_linked(self) -> None:
        text = "Jan Peeters et Marie Peeters ... Peeters"
        entities = [entity(text, "Jan Peeters"), entity(text, "Marie Peeters"), entity(text, "Peeters")]
        assert EntityLinker().link(entities)[2].canonical_text is None

    def test_initials_match_the_first_name(self) -> None:
        text = "Pieter Janssens ... P. JANSSENS ... M. Janssens"
        entities = [entity(text, "Pieter Janssens"), entity(text, "P. JANSSENS"), entity(text, "M. Janssens")]
        linked = EntityLinker().link(entities)
        assert [e.canonical_text for e in linked] == [None, "Pieter Janssens", None]
