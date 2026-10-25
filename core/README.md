# Core

Python engine and REST API (FastAPI) of the anonymiser. See the [main README](../README.md) for
how the system works and how to launch it.

## Code layout

| Path | Content |
|---|---|
| `src/belgian_anonymizer/extraction/` | PDF to Markdown with Docling, plus our corrections (hyphens at line breaks, paragraph splitting, reading order) |
| `src/belgian_anonymizer/detection/` | Recognizers (regex + checksums, GLiNER), then filtering, merging, propagation and linking of the detections |
| `src/belgian_anonymizer/anonymization/` | Placeholders (`[PERSON_1]`) and mapping |
| `src/belgian_anonymizer/rendering/` | PNG previews of the original PDF pages |
| `src/belgian_anonymizer/api/` | FastAPI routes and in-memory document store |
| `configs/` | `config-dev.json` (template) and `config-prod.json` (gitignored) |
| `scripts/` | Model download (run at image build time) and sample generation |
| `samples/` | Synthetic documents (FR/NL/DE/EN), generated from `tests/fixtures/sample_documents.py` |

## API

Interactive documentation: http://localhost:8000/docs.

| Method | Path | Description |
|---|---|---|
| `POST` | `/anonymize` | Upload a PDF (multipart `file`): original and anonymised Markdown, entities and mapping |
| `GET` | `/documents/{id}` | Same result as `/anonymize` |
| `GET` | `/documents/{id}/anonymized` | Anonymised Markdown (`?download=true` for an attachment) |
| `GET` | `/documents/{id}/pages/{n}` | PNG image of page `n` (0-based) of the original PDF |
| `GET` | `/documents/{id}/mapping` | Placeholder → original value table |
| `POST` | `/documents/{id}/deanonymize` | `{"text": "..."}`: puts the original values back in an LLM answer |
| `POST` | `/deanonymize` | Stateless variant: `{"text": "...", "mapping": [...]}` |
| `DELETE` | `/documents/{id}` | Forget a document, its PDF and its mapping |
| `GET` | `/health`, `/entity-types` | Status and enabled entity types |

Documents are kept in memory only (1 hour, 100 documents at most), which is why the API runs a
single worker.

Detected entity types: `PERSON`, `ORGANIZATION`, `ADDRESS`, `NATIONAL_NUMBER`, `ENTERPRISE_NUMBER`,
`IBAN`, `ID_CARD_NUMBER`, `PHONE`, `EMAIL`, `LICENSE_PLATE`, `DATE_OF_BIRTH`.

## Configuration

`configs/config-dev.json` is the template. For production, mount `configs/config-prod.json` and
set `ANONYMIZER_CONFIG_PATH` (see the commented lines in `docker-compose.yml`). Main settings:

| Setting | Purpose |
|---|---|
| `extraction.table_structure` | Detect tables (Markdown tables) |
| `extraction.image_placeholder` | Marker written where the document has an image (`[IMAGE]`) |
| `preview.dpi` | Resolution of the original page images |
| `detection.enabled_entity_types` | Entity types to anonymise |
| `detection.ner.threshold` | NER confidence: lower means fewer leaks but more false positives |
| `detection.ner.torch_threads`, `extraction.threads` | `0` = physical cores (using every hyper-thread is up to 10x slower) |
| `detection.contract_role_terms`, `person_titles`, `organization_legal_forms` | Word lists kept in clear text or used to link names |

## Development

Everything runs in Docker, nothing needs to be installed locally:

```bash
docker compose --profile test build core-tests   # once, and after a dependency change
./core/run-tests.sh -q                           # all tests, with live-mounted sources
./core/run-tests.sh -q -m "not ner"              # skip the slower NER tests
```

Dependencies are managed with `uv` (`pyproject.toml` + `uv.lock`). To regenerate the lock file:

```bash
docker run --rm -v "$PWD/core":/app -w /app ghcr.io/astral-sh/uv:0.8.17-python3.12-bookworm-slim uv lock
```

Only permissive licences are allowed (no GPL/AGPL). Check the licence of any new dependency or
model before adding it.
