"""Shared visible-output hygiene for provider and council layers.

Some transports can leak private reasoning or token-corruption artifacts into
visible assistant content. Cleaning at the provider boundary keeps council/audit
stages focused on ranking/audit logic, while council may still apply the same
helpers as a defensive backup.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

THINK_BLOCK_RE = re.compile(r"<think\b[^>]*>[\s\S]*?</think>", re.IGNORECASE)
UNCLOSED_THINK_RE = re.compile(r"<think\b[^>]*>[\s\S]*$", re.IGNORECASE)
LEADING_PARTIAL_TAG_RE = re.compile(r"^\s*<[A-Za-z]{1,24}(?=#{1,6}\s)")
VISIBLE_REASONING_PREAMBLE_RE = re.compile(
    r"(?is)^\s*(?:"
    # Keep this narrow: only private analysis openers, not legitimate answers.
    r"user\s+(?:is\s+trying|is\s+asking|message)\b|"
    r"the\s+user-message\s+is\b|"
    r"i(?:'m| am)\s+(?:looking|re-evaluating|trying|going|checking|reading)\b|"
    r"i\s+need\s+to\s+(?:verify|check|analyze|evaluate|assess|determine|parse|re-?evaluate|look|inspect|review)\b|"
    r"let\s+me\s+(?:think|check|re-?evaluate|verify|analyze|see|read|parse|assess|inspect|review)\b|"
    r"generating\s+evaluation\b"
    r")"
)
VISIBLE_REASONING_TRIM_TARGET_RE = re.compile(
    r"(?is)(```(?:json)?\s*\n|#{1,6}\s+(?:overall|threshold|assessment|analysis|strengths|evaluation|final|summary)\b|\{\s*\"responses\")"
)
TEXT_CORRUPTION_ARTIFACT_RE = re.compile(
    r"(?i)(^\s*<[A-Za-z]{1,24}(?=#{1,6}\s)|\bMempt\s+facts\b|\brelateected\b|\brespon\.\d|\btope\s+[?-]|\bqueming\b|\bsated\s+basis\b|\bex\s+available\s+sources\b)"
)


def strip_thinking_blocks(text: Any) -> str:
    """Remove hidden-reasoning markup from model-visible text."""

    cleaned = str(text or "").strip()
    cleaned = THINK_BLOCK_RE.sub("", cleaned)
    cleaned = UNCLOSED_THINK_RE.sub("", cleaned)
    return cleaned.strip()


def model_output_needs_hygiene_retry(text: Any) -> bool:
    """Detect visible reasoning leaks or token-corruption artifacts in output."""

    cleaned = strip_thinking_blocks(text)
    if not cleaned:
        return False
    return bool(
        VISIBLE_REASONING_PREAMBLE_RE.search(cleaned)
        or TEXT_CORRUPTION_ARTIFACT_RE.search(cleaned)
    )


def clean_model_visible_output(text: Any) -> str:
    """Clean visible output without changing substantive answer content.

    Handles provider leaks that arrive as visible content rather than hidden
    reasoning fields: partial tag prefixes before markdown headings and short
    analysis preambles before the actual answer/JSON payload.

    Truncation only runs when a private-reasoning preamble is present and a
    clear structural answer boundary exists. Ordinary answers that merely open
    with "User wants..." or "Let me walk you through..." are left intact.
    The operation is intentionally idempotent.
    """

    cleaned = strip_thinking_blocks(text)
    cleaned = LEADING_PARTIAL_TAG_RE.sub("", cleaned).strip()
    if VISIBLE_REASONING_PREAMBLE_RE.search(cleaned):
        match = VISIBLE_REASONING_TRIM_TARGET_RE.search(cleaned)
        if match and match.start() > 0:
            cleaned = cleaned[match.start():].strip()
            cleaned = LEADING_PARTIAL_TAG_RE.sub("", cleaned).strip()
    return cleaned


def build_output_hygiene_retry_messages(messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Append a narrow retry instruction for visible reasoning/corruption leaks."""

    retry_messages = list(messages or [])
    retry_messages.append({
        "role": "user",
        "content": (
            "RETRY: The prior answer contained visible private reasoning, planning text, "
            "or corrupted/truncated token fragments. Return only the final user-facing answer. "
            "Do not include analysis preambles such as 'user wants', 'I need to', or 'let me'. "
            "Do not include hidden reasoning. Ensure the answer text starts cleanly and is complete."
        ),
    })
    return retry_messages
