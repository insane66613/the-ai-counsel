from backend.output_hygiene import (
    clean_model_visible_output,
    model_output_needs_hygiene_retry,
    strip_thinking_blocks,
)


def test_strip_thinking_blocks_removes_complete_and_unclosed_markup():
    assert strip_thinking_blocks("<think>hidden</think>\n\nVisible answer") == "Visible answer"
    assert strip_thinking_blocks("<think>hidden only") == ""


def test_clean_model_visible_output_is_idempotent():
    dirty = "<l### Overall assessment\n\nBody"
    once = clean_model_visible_output(dirty)
    twice = clean_model_visible_output(once)
    assert once == twice
    assert once.startswith("### Overall assessment")


def test_legitimate_openers_are_not_flagged_or_mutated():
    samples = [
        "User wants a refund policy summary. Here it is: full refund within 30 days.",
        "Let me walk you through the steps to complete the form.",
        "I need to reset my password, can you help?",
        "User asked for the report; the answer follows with the numbers.",
    ]
    for raw in samples:
        assert model_output_needs_hygiene_retry(raw) is False
        assert clean_model_visible_output(raw) == raw


def test_true_reasoning_leak_still_trims_to_answer_boundary():
    raw = (
        "user is trying to apply a template and I need to verify statutes."
        "### Threshold framing\n\nThis is the answer."
    )
    assert model_output_needs_hygiene_retry(raw) is True
    assert clean_model_visible_output(raw) == "### Threshold framing\n\nThis is the answer."


def test_tool_action_preamble_trims_to_review_heading():
    raw = (
        "Let me search your workspace for any relevant context. "
        "data practices request ICR 25044901 AxonmLet me search again."
        "### Review of the Clarification Letter\n\nBody"
    )
    cleaned = clean_model_visible_output(raw)
    assert cleaned == "### Review of the Clarification Letter\n\nBody"
    assert model_output_needs_hygiene_retry(raw) is True


def test_corrupt_notion_citation_heading_recursion_requires_retry():
    raw = (
        "### Review of the Clarification Letter\n\n"
        "Text.[^{{notion-### Review of the Clarification Letter\n\n"
        "Text.[^{{notion-### Review of the Clarification Letter\n\n"
        "More text."
    )
    assert model_output_needs_hygiene_retry(raw) is True


def test_model_name_splice_artifacts_require_retry():
    samples = [
        "Sonnet 5owever the issue remains.",
        "DeepSeek V4 Proounty remains uncertain.",
        "## ****GLM 5.2PT-5.5hairman's Synthesis",
        "GLM 5.2rok 4.3 rankings were discussed.",
    ]
    for raw in samples:
        assert model_output_needs_hygiene_retry(raw) is True


def test_repeated_markdown_heading_requires_retry():
    raw = "\n".join([
        "### Review of the Clarification Letter",
        "first body",
        "### Review of the Clarification Letter",
        "second body",
        "### Review of the Clarification Letter",
        "third body",
    ])
    assert model_output_needs_hygiene_retry(raw) is True
