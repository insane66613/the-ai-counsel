"""Retest endpoints must read keys from the credential store (not settings.json)."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.credentials import file_backend, store


@pytest.fixture()
def cred_file(tmp_path, monkeypatch):
    path = tmp_path / "credentials.json"
    monkeypatch.setattr(file_backend, "CREDENTIALS_FILE", path)
    monkeypatch.setattr(store, "get_effective_mode", lambda: "file")
    monkeypatch.setattr(store, "_preferred_mode", lambda: "file")
    monkeypatch.setattr(store, "ENV_OVERRIDES", {})
    monkeypatch.setattr(store, "_disabled_secret_ids", lambda: set())
    yield path


@pytest.fixture()
def client(cred_file):
    from backend.main import app

    with TestClient(app, client=("127.0.0.1", 50000)) as c:
        yield c


def test_retest_uses_stored_anthropic_key(client, cred_file):
    store.set_secret("api:anthropic", "sk-ant-from-store")
    mock_validate = AsyncMock(return_value={"success": True, "message": "ok"})

    with patch("backend.providers.anthropic.AnthropicProvider.validate_key", mock_validate):
        resp = client.post(
            "/api/settings/test-provider",
            json={"provider_id": "anthropic", "api_key": ""},
        )

    assert resp.status_code == 200
    assert resp.json()["success"] is True
    mock_validate.assert_awaited_once_with("sk-ant-from-store")


def test_retest_without_store_or_request_fails(client, cred_file):
    resp = client.post(
        "/api/settings/test-provider",
        json={"provider_id": "anthropic", "api_key": ""},
    )
    assert resp.status_code == 200
    assert resp.json() == {
        "success": False,
        "message": "No API key provided or configured",
    }


class _NotionStatusResponse:
    status_code = 200

    @staticmethod
    def json():
        return {"data": [{"id": "terra"}]}


class _NotionStatusClient:
    captured_headers = None

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, *, headers=None):
        type(self).captured_headers = dict(headers or {})
        return _NotionStatusResponse()


def test_notion2api_retest_uses_stored_key(client, cred_file):
    store.set_secret("api:notion2api", "n2-from-store")
    mock_validate = AsyncMock(return_value={"success": True, "message": "ok"})

    with patch(
        "backend.providers.notion2api.Notion2APIProvider.validate_connection",
        mock_validate,
    ):
        resp = client.post(
            "/api/settings/test-notion2api",
            json={"url": "http://127.0.0.1:8120/v1", "api_key": ""},
        )

    assert resp.status_code == 200
    assert resp.json()["success"] is True
    mock_validate.assert_awaited_once_with("http://127.0.0.1:8120/v1", "n2-from-store")


def test_notion2api_status_uses_stored_key(client, cred_file, monkeypatch):
    import httpx

    store.set_secret("api:notion2api", "n2-from-store")
    _NotionStatusClient.captured_headers = None
    monkeypatch.setattr(httpx, "AsyncClient", _NotionStatusClient)

    resp = client.get("/api/notion2api/status")

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["running"] is True
    assert payload["api_key_set"] is True
    assert payload["model_count"] == 1
    assert _NotionStatusClient.captured_headers == {"Authorization": "Bearer n2-from-store"}
