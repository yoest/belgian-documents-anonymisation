#!/usr/bin/env bash
# Runs the test suite with live-mounted sources, so no rebuild is needed after a code change.
# Build the test image first (and after a dependency change): docker compose --profile test build core-tests
CORE="$(cd "$(dirname "$0")" && pwd)"
docker run --rm \
  -v "$CORE/src:/app/src:Z" -v "$CORE/tests:/app/tests:Z" -v "$CORE/configs:/app/configs:Z" \
  belgian-anonymizer-core-dev uv run --no-sync pytest -p no:cacheprovider "$@"
