from types import SimpleNamespace

import pytest

from scripts import qualify_audit_pipeline as qualification


@pytest.mark.asyncio
async def test_qualification_preflight_uses_durable_notion2api_key(monkeypatch):
    captured = {}

    class FakeProvider:
        async def validate_connection(self, url, token):
            captured["url"] = url
            captured["token"] = token
            return {"success": True, "message": "ok"}

        async def get_models(self):
            return [{"id": "notion2api:terra", "aliases": []}]

    async def fake_preflight(models, timeout):
        captured["models"] = list(models)
        captured["timeout"] = timeout
        return SimpleNamespace(failures=[], timeouts=[], rate_limited=[])

    monkeypatch.setattr(
        qualification,
        "get_settings",
        lambda: SimpleNamespace(
            notion2api_base_url="http://127.0.0.1:8120/v1",
            preflight_timeout_seconds=15,
        ),
    )
    monkeypatch.setattr(qualification, "resolve_api_key", lambda provider: "stored-n2-key")
    monkeypatch.setattr(qualification, "Notion2APIProvider", FakeProvider)
    monkeypatch.setattr(qualification, "preflight_models", fake_preflight)

    ok, message = await qualification._provider_preflight(["notion2api:terra"], "notion2api:terra")

    assert ok is True
    assert message == "provider preflight passed"
    assert captured["token"] == "stored-n2-key"
    assert captured["url"] == "http://127.0.0.1:8120/v1"
    assert captured["timeout"] == 15
