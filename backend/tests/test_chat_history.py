from __future__ import annotations

from backend.main import _build_chat_history


def test_builds_history_from_normal_conversation():
    conversation = {
        "messages": [
            {"role": "user", "content": "What is AI?"},
            {"role": "assistant", "stage1": [{"response": "AI is..."}], "stage3": {"response": "AI is artificial intelligence."}},
            {"role": "user", "content": "Tell me more."},
        ]
    }
    history = _build_chat_history(conversation)
    assert len(history) == 3
    assert history[0] == {"role": "user", "content": "What is AI?"}
    assert history[1] == {"role": "assistant", "content": "AI is artificial intelligence."}
    assert history[2] == {"role": "user", "content": "Tell me more."}


def test_skips_messages_without_role():
    conversation = {
        "messages": [
            {"content": "orphan"},
            {"role": "user", "content": "Hello"},
        ]
    }
    history = _build_chat_history(conversation)
    assert len(history) == 1
    assert history[0] == {"role": "user", "content": "Hello"}


def test_handles_corrupt_stage3():
    conversation = {
        "messages": [
            {"role": "assistant", "stage3": True},
            {"role": "user", "content": "Next"},
        ]
    }
    history = _build_chat_history(conversation)
    assert len(history) == 1
    assert history[0] == {"role": "user", "content": "Next"}


def test_handles_corrupt_stage1():
    conversation = {
        "messages": [
            {"role": "assistant", "stage1": "not_a_list"},
            {"role": "user", "content": "Next"},
        ]
    }
    history = _build_chat_history(conversation)
    assert len(history) == 1
    assert history[0] == {"role": "user", "content": "Next"}


def test_handles_non_dict_messages():
    conversation = {
        "messages": [
            "not a dict",
            None,
            {"role": "user", "content": "Legit"},
        ]
    }
    history = _build_chat_history(conversation)
    assert len(history) == 1
    assert history[0] == {"role": "user", "content": "Legit"}


def test_falls_back_to_stage1_when_stage3_missing():
    conversation = {
        "messages": [
            {"role": "assistant", "stage1": [{"response": "First stage response"}]},
        ]
    }
    history = _build_chat_history(conversation)
    assert len(history) == 1
    assert history[0] == {"role": "assistant", "content": "First stage response"}


def test_skips_errors_in_stage1():
    conversation = {
        "messages": [
            {"role": "assistant", "stage1": [
                {"error": True, "error_message": "fail"},
                {"response": "Success response"},
            ]},
        ]
    }
    history = _build_chat_history(conversation)
    assert len(history) == 1
    assert history[0] == {"role": "assistant", "content": "Success response"}


def test_returns_empty_for_empty_conversation():
    history = _build_chat_history({"messages": []})
    assert history == []
