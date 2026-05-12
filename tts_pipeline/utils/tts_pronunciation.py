"""
Plain-text pronunciation hints for Azure batch TTS (inputKind: PlainText).

Replaces whole words (and optional possessives) with alternate spellings so the
voice reads them as intended. Applied to chapter text immediately before batch
submission in azure_tts_client._load_chapter_text.

Disable built-in rules: set processing_config.pronunciation_disable_defaults to true.
Add more words: processing_config.pronunciation_substitutions (list of dicts).
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

# Applied unless pronunciation_disable_defaults is true in processing_config.
DEFAULT_SUBSTITUTIONS: List[Dict[str, Any]] = [
    {
        "word": "Lumian",
        "spoken_as": "Loomian",
        "include_possessive": True,
        "case_insensitive": True,
    },
]


def _match_case(spoken: str, original: str) -> str:
    if original.isupper():
        return spoken.upper()
    if len(original) > 1 and original[0].isupper() and original[1:].islower():
        return spoken[0].upper() + spoken[1:]
    if original[0].isupper():
        return spoken[0].upper() + spoken[1:]
    return spoken


def apply_pronunciation_substitutions(
    text: str,
    user_rules: Optional[List[Dict[str, Any]]] = None,
    *,
    disable_defaults: bool = False,
) -> str:
    if not text:
        return text

    rules: List[Dict[str, Any]] = []
    if not disable_defaults:
        rules.extend(DEFAULT_SUBSTITUTIONS)
    if user_rules:
        rules.extend(user_rules)

    out = text
    for rule in rules:
        word = (rule.get("word") or "").strip()
        spoken = (rule.get("spoken_as") or "").strip()
        if not word or not spoken:
            continue
        possessive = bool(rule.get("include_possessive", True))
        ci = bool(rule.get("case_insensitive", True))

        esc = re.escape(word)
        if possessive:
            pat = rf"(?<![A-Za-z0-9]){esc}(?:'s)?(?![A-Za-z0-9])"
        else:
            pat = rf"(?<![A-Za-z0-9]){esc}(?![A-Za-z0-9])"
        flags = re.IGNORECASE if ci else 0

        def repl(m: re.Match) -> str:
            full = m.group(0)
            low = full.lower()
            lw = word.lower()
            if low == lw:
                return _match_case(spoken, full)
            if possessive and low == lw + "'s":
                stem = _match_case(spoken, full[: -len("'s")])
                return stem + "'s"
            return full

        out = re.sub(pat, repl, out, flags=flags)

    return out
