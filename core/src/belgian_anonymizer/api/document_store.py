import threading
import time
import uuid
from collections import OrderedDict
from dataclasses import dataclass

from belgian_anonymizer.models.result import AnonymizationResult


@dataclass(frozen=True, slots=True)
class StoredDocument:
    document_id: str
    result: AnonymizationResult
    expires_at: float


class InMemoryDocumentStore:
    """Keeps results (including the mapping) in memory only, for a limited time.

    Nothing is written to disk, so a restart wipes everything. Requires a single API worker.
    """

    def __init__(self, ttl_seconds: int, max_documents: int) -> None:
        self._ttl = ttl_seconds
        self._max_documents = max_documents
        self._documents: OrderedDict[str, StoredDocument] = OrderedDict()
        self._lock = threading.Lock()

    def add(self, result: AnonymizationResult) -> StoredDocument:
        stored = StoredDocument(uuid.uuid4().hex, result, time.monotonic() + self._ttl)
        with self._lock:
            self._evict_expired()
            self._documents[stored.document_id] = stored
            while len(self._documents) > self._max_documents:
                self._documents.popitem(last=False)
        return stored

    def get(self, document_id: str) -> StoredDocument | None:
        with self._lock:
            self._evict_expired()
            return self._documents.get(document_id)

    def delete(self, document_id: str) -> bool:
        with self._lock:
            return self._documents.pop(document_id, None) is not None

    def _evict_expired(self) -> None:
        now = time.monotonic()
        for document_id in [key for key, stored in self._documents.items() if stored.expires_at <= now]:
            del self._documents[document_id]
