import importlib.util
from collections.abc import Callable

import pytest

from belgian_anonymizer.config import AppConfig
from belgian_anonymizer.pipeline import AnonymizationPipeline
from tests.fixtures.contract_factory import ContractPdfFactory, SyntheticContract, dutch_lease, french_lease

pytestmark = [
    pytest.mark.ner,
    pytest.mark.skipif(importlib.util.find_spec("gliner") is None, reason="gliner is not installed"),
]


@pytest.fixture(scope="module")
def full_pipeline(dev_config: AppConfig) -> AnonymizationPipeline:
    return AnonymizationPipeline.from_config(dev_config)


def test_every_sensitive_value_is_removed(
    full_pipeline: AnonymizationPipeline, pdf_factory: ContractPdfFactory, contract: SyntheticContract
) -> None:
    result = full_pipeline.run(pdf_factory.build(contract), contract.filename)

    leaks = [value for value in contract.sensitive_values if value in result.anonymized_text]
    lost = [value for value in contract.kept_values if value not in result.anonymized_text]
    assert (leaks, lost) == ([], [])


@pytest.mark.parametrize("build_contract", [french_lease, dutch_lease], ids=["fr", "nl"])
def test_party_keeps_one_placeholder_across_the_document(
    full_pipeline: AnonymizationPipeline,
    pdf_factory: ContractPdfFactory,
    build_contract: Callable[[], SyntheticContract],
) -> None:
    contract = build_contract()
    result = full_pipeline.run(pdf_factory.build(contract), contract.filename)
    persons = {item.placeholder for item in result.entities if item.entity.entity_type == "PERSON"}
    # Each synthetic contract has exactly two natural persons, whatever the casing or form used
    assert len(persons) == 2
