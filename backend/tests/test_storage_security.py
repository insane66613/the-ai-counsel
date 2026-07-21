import json

import pytest

from backend import storage
from backend.json_files import atomic_write_json


@pytest.mark.parametrize("conversation_id", ["../settings", r"..\settings", "conversation/child"])
def test_conversation_path_rejects_traversal(tmp_path, monkeypatch, conversation_id):
    conversations_dir = tmp_path / "conversations"
    conversations_dir.mkdir()
    protected = tmp_path / "settings.json"
    protected.write_text('{"secret": true}', encoding="utf-8")
    monkeypatch.setattr(storage, "DATA_DIR", str(conversations_dir))

    assert storage.delete_conversation(conversation_id) is False
    assert protected.exists()


def test_conversation_path_accepts_legacy_safe_ids(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_DIR", str(tmp_path))

    assert storage.get_conversation_path("legacy-conversation_01") == str(tmp_path / "legacy-conversation_01.json")


def test_atomic_json_write_preserves_existing_file_when_replace_fails(tmp_path, monkeypatch):
    target = tmp_path / "state.json"
    target.write_text('{"version": 1}', encoding="utf-8")

    def fail_replace(*_args):
        raise OSError("simulated replace failure")

    monkeypatch.setattr("backend.json_files.os.replace", fail_replace)

    with pytest.raises(OSError, match="simulated replace failure"):
        atomic_write_json(target, {"version": 2})

    assert json.loads(target.read_text(encoding="utf-8")) == {"version": 1}
    assert list(tmp_path.glob(".state.json.*.tmp")) == []
