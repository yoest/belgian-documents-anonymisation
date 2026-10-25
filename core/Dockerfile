FROM python:3.12-slim-bookworm AS base
COPY --from=ghcr.io/astral-sh/uv:0.8.17 /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_CACHE=1 \
    UV_PYTHON_DOWNLOADS=0 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HF_HOME=/models/huggingface
WORKDIR /app

# Third-party dependencies only, so this layer is cached until uv.lock changes
FROM base AS deps
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# NER models are baked into the image so the container never needs internet at runtime
FROM deps AS models
COPY configs/config-dev.json ./configs/config-dev.json
COPY scripts/download_models.py ./scripts/download_models.py
RUN uv run --no-sync python scripts/download_models.py --config configs/config-dev.json

FROM deps AS app
COPY src ./src
COPY configs ./configs
RUN uv sync --frozen --no-dev

# Test image: dev dependencies + tests, run with `docker compose run --rm core-tests`
FROM app AS dev
RUN uv sync --frozen
COPY --from=models /models /models
COPY tests ./tests
COPY scripts ./scripts
ENV HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
CMD ["uv", "run", "--no-sync", "pytest", "-q"]

FROM python:3.12-slim-bookworm AS runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    HF_HOME=/models/huggingface \
    HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1 \
    ANONYMIZER_CONFIG_PATH=/app/configs/config-dev.json
RUN useradd --create-home --uid 10001 anonymizer
WORKDIR /app
COPY --from=app --chown=anonymizer:anonymizer /app /app
COPY --from=models --chown=anonymizer:anonymizer /models /models
USER anonymizer
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"
CMD ["python", "-m", "belgian_anonymizer"]
