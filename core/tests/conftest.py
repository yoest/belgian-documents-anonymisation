from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from belgian_anonymizer.api import create_app
from belgian_anonymizer.config import AppConfig
from belgian_anonymizer.pipeline import AnonymizationPipeline
from tests.fixtures.contract_factory import ContractPdfFactory, SyntheticContract
from tests.fixtures.sample_documents import SAMPLE_DOCUMENTS


@pytest.fixture(scope="session")
def dev_config() -> AppConfig:
    return AppConfig.load()


@pytest.fixture(scope="session")
def pattern_config(dev_config: AppConfig) -> AppConfig:
    # Regex/checksum recognizers only: fast, deterministic and independent of the NER model
    config = dev_config.model_copy(deep=True)
    config.detection.ner.enabled = False
    return config


@pytest.fixture(scope="session")
def pattern_pipeline(pattern_config: AppConfig) -> AnonymizationPipeline:
    return AnonymizationPipeline.from_config(pattern_config)


@pytest.fixture(scope="session")
def pdf_factory() -> ContractPdfFactory:
    return ContractPdfFactory()


@pytest.fixture(params=SAMPLE_DOCUMENTS, ids=[build.__name__ for build in SAMPLE_DOCUMENTS])
def contract(request: pytest.FixtureRequest) -> SyntheticContract:
    contract: SyntheticContract = request.param()
    return contract


@pytest.fixture
def client(pattern_config: AppConfig, pattern_pipeline: AnonymizationPipeline) -> Iterator[TestClient]:
    with TestClient(create_app(pattern_config, pattern_pipeline)) as test_client:
        yield test_client
