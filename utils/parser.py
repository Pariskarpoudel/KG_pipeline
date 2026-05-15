# utils/parser.py
import json
import re
import logging
from typing import Any

logger = logging.getLogger(__name__)


def _remove_trailing_commas(s: str) -> str:
    prev = ""
    while s != prev:
        prev = s
        s = re.sub(r',\s*([}\]])', r'\1', s)
    return s


def parse_llm_json(raw_text: str, expected_type: str = "auto") -> Any:
    """
    Extract JSON from raw LLM output.
    Handles: markdown fences, prose before/after JSON, trailing commas.

    expected_type: "list"  → triples, concepts, definitions
                   "dict"  → entity resolution, single relation
                   "auto"  → no check, return whatever parses
    Returns None on failure.
    """
    if not raw_text or not raw_text.strip():
        logger.warning("Parser: empty input")
        return None

    text = raw_text.strip()

    # Step 1: Strip markdown fences
    text = re.sub(r'^\s*```(?:json)?\s*\n?', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\n?```\s*$', '', text, flags=re.IGNORECASE)
    text = text.strip()

    # Step 2: Direct parse — happy path
    try:
        return _check_type(json.loads(text), expected_type)
    except json.JSONDecodeError:
        pass

    # Step 3: Find JSON block inside surrounding prose
    match = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', text, re.DOTALL)
    if match:
        # Step 3a: Direct parse of extracted block
        try:
            return _check_type(json.loads(match.group(1)), expected_type)
        except json.JSONDecodeError:
            pass
        # Step 3b: Fix trailing commas on extracted block and retry
        try:
            return _check_type(json.loads(_remove_trailing_commas(match.group(1))), expected_type)
        except json.JSONDecodeError:
            pass

    # Step 4: Fix trailing commas on full text and retry
    fixed = _remove_trailing_commas(text)
    try:
        return _check_type(json.loads(fixed), expected_type)
    except json.JSONDecodeError:
        pass

    logger.warning(f"Parser failed. Preview:\n{text[:300]}")
    return None


def _check_type(parsed: Any, expected: str) -> Any:
    if expected == "auto":
        return parsed
    if expected == "list" and isinstance(parsed, list):
        return parsed
    if expected == "dict" and isinstance(parsed, dict):
        return parsed
    logger.warning(f"Type mismatch: expected {expected}, got {type(parsed).__name__}")
    return None