from typing import Annotated, Any
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, HTTPException, Request, Response, UploadFile, status

from belgian_anonymizer.api.document_store import InMemoryDocumentStore, StoredDocument
from belgian_anonymizer.api.schemas import (
    AnonymizeResponse,
    DeanonymizeRequest,
    DeanonymizeResponse,
    DocumentDeanonymizeRequest,
    ErrorResponse,
    HealthResponse,
    MappingEntrySchema,
)
from belgian_anonymizer.config import AppConfig
from belgian_anonymizer.extraction import PdfExtractionError
from belgian_anonymizer.models.entity import EntityType
from belgian_anonymizer.models.mapping import AnonymizationMapping
from belgian_anonymizer.pipeline import AnonymizationPipeline
from belgian_anonymizer.rendering import PageOutOfRangeError, PdfPageRenderer

_READ_CHUNK_BYTES = 1024 * 1024
_NOT_FOUND: dict[int | str, dict[str, Any]] = {
    404: {"model": ErrorResponse, "description": "Unknown or expired document"}
}


def get_pipeline(request: Request) -> AnonymizationPipeline:
    pipeline: AnonymizationPipeline = request.app.state.pipeline
    return pipeline


def get_store(request: Request) -> InMemoryDocumentStore:
    store: InMemoryDocumentStore = request.app.state.store
    return store


def get_config(request: Request) -> AppConfig:
    config: AppConfig = request.app.state.config
    return config


def get_page_renderer(request: Request) -> PdfPageRenderer:
    renderer: PdfPageRenderer = request.app.state.page_renderer
    return renderer


def get_document(
    document_id: str, store: Annotated[InMemoryDocumentStore, Depends(get_store)]
) -> StoredDocument:
    stored = store.get(document_id)
    if stored is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown or expired document.")
    return stored


PipelineDep = Annotated[AnonymizationPipeline, Depends(get_pipeline)]
StoreDep = Annotated[InMemoryDocumentStore, Depends(get_store)]
ConfigDep = Annotated[AppConfig, Depends(get_config)]
DocumentDep = Annotated[StoredDocument, Depends(get_document)]
PageRendererDep = Annotated[PdfPageRenderer, Depends(get_page_renderer)]

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["system"])
def health(config: ConfigDep) -> HealthResponse:
    return HealthResponse(status="ok", ner_enabled=config.detection.ner.enabled)


@router.get("/entity-types", response_model=list[EntityType], tags=["system"])
def entity_types(pipeline: PipelineDep) -> list[EntityType]:
    return sorted(pipeline.enabled_types)


@router.post(
    "/anonymize",
    response_model=AnonymizeResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["anonymization"],
    responses={
        413: {"model": ErrorResponse, "description": "File too large"},
        422: {"model": ErrorResponse, "description": "Not a supported PDF"},
    },
)
def anonymize(
    file: Annotated[UploadFile, File(description="Text-based PDF document")],
    pipeline: PipelineDep,
    store: StoreDep,
    config: ConfigDep,
) -> AnonymizeResponse:
    # Sync endpoint on purpose: FastAPI runs it in a thread pool, so CPU-bound NER does not block the loop
    content = _read_limited(file, config.api.max_upload_size_mb * 1024 * 1024)
    try:
        result = pipeline.run(content, file.filename or "document.pdf")
    except PdfExtractionError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    return AnonymizeResponse.from_stored(store.add(result))


@router.get(
    "/documents/{document_id}", response_model=AnonymizeResponse, tags=["documents"], responses=_NOT_FOUND
)
def get_result(stored: DocumentDep) -> AnonymizeResponse:
    return AnonymizeResponse.from_stored(stored)


@router.get(
    "/documents/{document_id}/anonymized",
    response_class=Response,
    tags=["documents"],
    responses={200: {"content": {"text/markdown": {}}}, **_NOT_FOUND},
)
def get_anonymized_text(stored: DocumentDep, download: bool = False) -> Response:
    stem = stored.result.document.filename.rsplit(".", 1)[0]
    content = stored.result.anonymized_text.encode("utf-8")
    return _file_response(content, "text/markdown; charset=utf-8", f"{stem}-anonymized.md", download)


@router.get(
    "/documents/{document_id}/pages/{page_number}",
    response_class=Response,
    tags=["documents"],
    responses={200: {"content": {"image/png": {}}}, **_NOT_FOUND},
)
def get_page_preview(stored: DocumentDep, page_number: int, renderer: PageRendererDep) -> Response:
    """PNG image of one page (0-based) of the original PDF, for previews."""
    try:
        image = renderer.render_png(stored.result.document.content, page_number)
    except PageOutOfRangeError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Page out of range.") from error
    return Response(content=image, media_type="image/png", headers={"Cache-Control": "no-store"})


@router.get(
    "/documents/{document_id}/mapping",
    response_model=list[MappingEntrySchema],
    tags=["documents"],
    responses=_NOT_FOUND,
)
def get_mapping(stored: DocumentDep) -> list[MappingEntrySchema]:
    return [MappingEntrySchema.from_entry(entry) for entry in stored.result.mapping.entries]


@router.post(
    "/documents/{document_id}/deanonymize",
    response_model=DeanonymizeResponse,
    tags=["documents"],
    responses=_NOT_FOUND,
)
def deanonymize_document(stored: DocumentDep, body: DocumentDeanonymizeRequest) -> DeanonymizeResponse:
    return _restore(stored.result.mapping, body.text)


@router.delete(
    "/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["documents"],
    responses=_NOT_FOUND,
)
def delete_document(document_id: str, store: StoreDep) -> Response:
    if not store.delete(document_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown or expired document.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/deanonymize", response_model=DeanonymizeResponse, tags=["anonymization"])
def deanonymize(body: DeanonymizeRequest) -> DeanonymizeResponse:
    # Stateless variant: the client keeps the mapping itself (e.g. after the document expired)
    return _restore(AnonymizationMapping([entry.to_entry() for entry in body.mapping]), body.text)


def _restore(mapping: AnonymizationMapping, text: str) -> DeanonymizeResponse:
    restored, replaced, unknown = mapping.restore(text)
    return DeanonymizeResponse(text=restored, replaced_count=replaced, unknown_placeholders=unknown)


def _read_limited(file: UploadFile, max_bytes: int) -> bytes:
    chunks: list[bytes] = []
    size = 0
    while chunk := file.file.read(_READ_CHUNK_BYTES):
        size += len(chunk)
        if size > max_bytes:
            raise HTTPException(
                status.HTTP_413_CONTENT_TOO_LARGE, f"File exceeds {max_bytes // (1024 * 1024)} MB."
            )
        chunks.append(chunk)
    return b"".join(chunks)


def _file_response(content: bytes, media_type: str, filename: str, download: bool) -> Response:
    disposition = "attachment" if download else "inline"
    headers = {
        "Content-Disposition": f"{disposition}; filename*=UTF-8''{quote(filename)}",
        # Documents hold personal data: never let browsers or proxies cache them
        "Cache-Control": "no-store",
    }
    return Response(content=content, media_type=media_type, headers=headers)
