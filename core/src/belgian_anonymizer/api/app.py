from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from belgian_anonymizer.api.document_store import InMemoryDocumentStore
from belgian_anonymizer.api.routes import router
from belgian_anonymizer.config import AppConfig
from belgian_anonymizer.pipeline import AnonymizationPipeline
from belgian_anonymizer.rendering import PdfPageRenderer


def create_app(config: AppConfig | None = None, pipeline: AnonymizationPipeline | None = None) -> FastAPI:
    """Builds the API; tests can inject a lightweight pipeline instead of loading the NER model."""
    app_config = config or AppConfig.load()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        # The NER model is loaded once at startup rather than on the first request
        app.state.pipeline = pipeline or AnonymizationPipeline.from_config(app_config)
        app.state.pipeline.warm_up()
        yield

    app = FastAPI(
        title="Belgian Documents Anonymizer",
        description="Reversible anonymisation of Belgian contracts (PDF) before sending them to LLMs.",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.config = app_config
    app.state.store = InMemoryDocumentStore(app_config.store.ttl_seconds, app_config.store.max_documents)
    app.state.page_renderer = PdfPageRenderer(app_config.preview.dpi)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_config.api.cors_origins,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["*"],
        expose_headers=["Content-Disposition"],
    )
    app.include_router(router)
    return app
