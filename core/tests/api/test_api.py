from fastapi.testclient import TestClient

from tests.fixtures.contract_factory import ContractPdfFactory, french_lease


def upload(client: TestClient, content: bytes, filename: str = "bail.pdf") -> dict[str, object]:
    response = client.post("/anonymize", files={"file": (filename, content, "application/pdf")})
    assert response.status_code == 201, response.text
    body: dict[str, object] = response.json()
    return body


class TestAnonymizeEndpoint:
    def test_returns_texts_entities_and_mapping(
        self, client: TestClient, pdf_factory: ContractPdfFactory
    ) -> None:
        body = upload(client, pdf_factory.build(french_lease()))

        assert body["page_count"] == 2
        assert "[NATIONAL_NUMBER_1]" in str(body["anonymized_text"])
        assert isinstance(body["entities"], list) and body["entities"]
        mapping = {entry["placeholder"]: entry for entry in body["mapping"]}  # type: ignore[attr-defined]
        assert mapping["[EMAIL_1]"]["value"] == "jan.peeters@example.be"

    def test_rejects_non_pdf(self, client: TestClient) -> None:
        response = client.post("/anonymize", files={"file": ("notes.txt", b"hello", "text/plain")})
        assert response.status_code == 422
        assert "not a PDF" in response.json()["detail"]

    def test_rejects_too_large_file(self, client: TestClient) -> None:
        too_large = b"%PDF-" + b"0" * (21 * 1024 * 1024)
        response = client.post("/anonymize", files={"file": ("big.pdf", too_large, "application/pdf")})
        assert response.status_code == 413


class TestDocumentEndpoints:
    def test_exports_anonymized_text(self, client: TestClient, pdf_factory: ContractPdfFactory) -> None:
        document_id = upload(client, pdf_factory.build(french_lease()))["document_id"]

        response = client.get(f"/documents/{document_id}/anonymized", params={"download": True})

        assert response.headers["content-type"].startswith("text/markdown")
        assert response.headers["content-disposition"].startswith("attachment;")
        assert "bail-anonymized.md" in response.headers["content-disposition"]
        assert response.headers["cache-control"] == "no-store"
        assert "[IBAN_1]" in response.text
        assert "jan.peeters@example.be" not in response.text

    def test_original_pages_are_served_as_images(
        self, client: TestClient, pdf_factory: ContractPdfFactory
    ) -> None:
        document_id = upload(client, pdf_factory.build(french_lease()))["document_id"]

        response = client.get(f"/documents/{document_id}/pages/0")

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        assert response.headers["cache-control"] == "no-store"
        assert response.content.startswith(b"\x89PNG")
        assert client.get(f"/documents/{document_id}/pages/2").status_code == 404
        assert client.get(f"/documents/{document_id}/original").status_code == 404

    def test_deanonymizes_llm_answer(self, client: TestClient, pdf_factory: ContractPdfFactory) -> None:
        document_id = upload(client, pdf_factory.build(french_lease()))["document_id"]
        answer = "Write to [EMAIL_1] about [UNKNOWN_1]."

        response = client.post(f"/documents/{document_id}/deanonymize", json={"text": answer})

        assert response.json() == {
            "text": "Write to jan.peeters@example.be about [UNKNOWN_1].",
            "replaced_count": 1,
            "unknown_placeholders": ["[UNKNOWN_1]"],
        }

    def test_stateless_deanonymize(self, client: TestClient) -> None:
        mapping = [{"placeholder": "[PERSON_1]", "entity_type": "PERSON", "value": "Jan Peeters"}]
        response = client.post("/deanonymize", json={"text": "Hello [PERSON_1]", "mapping": mapping})
        assert response.json()["text"] == "Hello Jan Peeters"

    def test_delete_then_not_found(self, client: TestClient, pdf_factory: ContractPdfFactory) -> None:
        document_id = upload(client, pdf_factory.build(french_lease()))["document_id"]
        assert client.delete(f"/documents/{document_id}").status_code == 204
        assert client.get(f"/documents/{document_id}").status_code == 404
        assert client.get(f"/documents/{document_id}/mapping").status_code == 404


class TestSystemEndpoints:
    def test_health(self, client: TestClient) -> None:
        assert client.get("/health").json() == {"status": "ok", "ner_enabled": False}

    def test_entity_types(self, client: TestClient) -> None:
        assert "NATIONAL_NUMBER" in client.get("/entity-types").json()
