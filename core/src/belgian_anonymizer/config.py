import os
from pathlib import Path

from pydantic import BaseModel, Field

from belgian_anonymizer.models.entity import EntityType

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "configs" / "config-dev.json"
CONFIG_PATH_ENV_VAR = "ANONYMIZER_CONFIG_PATH"


class ApiConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    max_upload_size_mb: int = 20
    cors_origins: list[str] = Field(default_factory=list)


class StoreConfig(BaseModel):
    ttl_seconds: int = 3600
    max_documents: int = 100


class NerConfig(BaseModel):
    enabled: bool = True
    model_name: str = "urchade/gliner_multi_pii-v1"
    threshold: float = 0.4
    chunk_size_words: int = 200
    chunk_overlap_words: int = 40
    # 0 = auto (physical cores). Using every logical CPU (hyper-threads) makes inference ~10x slower
    torch_threads: int = 0
    labels: dict[str, EntityType] = Field(default_factory=dict)


class ExtractionConfig(BaseModel):
    # Docling layout and table models, downloaded at image build time (scripts/download_models.py)
    models_dir: str = "/models/docling"
    table_structure: bool = True
    # Marker written in the Markdown where the document has an image
    image_placeholder: str = "[IMAGE]"
    timeout_seconds: float = 300
    # 0 = auto (physical cores)
    threads: int = 0


class PreviewConfig(BaseModel):
    # Resolution of the original page images served by /documents/{id}/pages/{n}
    dpi: int = 110


class PropagationConfig(BaseModel):
    enabled: bool = True
    propagate_name_parts: bool = True
    min_name_part_length: int = 3


class DetectionConfig(BaseModel):
    enabled_entity_types: list[EntityType] = Field(default_factory=lambda: list(EntityType))
    ner: NerConfig = Field(default_factory=NerConfig)
    propagation: PropagationConfig = Field(default_factory=PropagationConfig)
    contract_role_terms: list[str] = Field(default_factory=list)
    name_particles: list[str] = Field(default_factory=list)
    person_titles: list[str] = Field(default_factory=list)
    organization_legal_forms: list[str] = Field(default_factory=list)


class LoggingConfig(BaseModel):
    level: str = "INFO"


class AppConfig(BaseModel):
    api: ApiConfig = Field(default_factory=ApiConfig)
    store: StoreConfig = Field(default_factory=StoreConfig)
    extraction: ExtractionConfig = Field(default_factory=ExtractionConfig)
    preview: PreviewConfig = Field(default_factory=PreviewConfig)
    detection: DetectionConfig = Field(default_factory=DetectionConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    @classmethod
    def load(cls, path: Path | None = None) -> "AppConfig":
        # Explicit path first, then the environment variable, then the dev template
        resolved = path or Path(os.environ.get(CONFIG_PATH_ENV_VAR, DEFAULT_CONFIG_PATH))
        return cls.model_validate_json(resolved.read_text(encoding="utf-8"))
