"""Parse + normalize LLM output into domain models.

"""

from __future__ import annotations

import json
import re
from typing import Any

from pydantic import BaseModel, ValidationError

from localis.core.errors import ParsingError
from localis.core.logging import get_logger

logger = get_logger(__name__)

# -- Cleaning --------------------------------------------------------------------

# Catches the wide blocks of emojis / pictographs that LLMs like to sprinkle.
_EMOJI_PATTERN = re.compile(
    "["
    "\U0001f600-\U0001f64f"  # emoticons
    "\U0001f300-\U0001f5ff"  # symbols & pictographs
    "\U0001f680-\U0001f6ff"  # transport
    "\U0001f1e0-\U0001f1ff"  # flags
    "\U00002702-\U000027b0"
    "\U000024c2-\U0001f251"
    "]+",
    flags=re.UNICODE,
)

_CODE_FENCE_PATTERN = re.compile(r"```(?:json|JSON)?\s*(.*?)```", re.DOTALL)
_JSON_OBJECT_PATTERN = re.compile(r"\{.*\}", re.DOTALL)


def strip_emojis(text: str) -> str:
    return _EMOJI_PATTERN.sub("", text)


def clean_text(text: str) -> str:
    """Normalize whitespace, strip emojis. Safe for both free-text and JSON input."""
    if not text:
        return ""
    cleaned = strip_emojis(text)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def extract_json_block(text: str) -> str:
    """Pull the first JSON object out of arbitrary LLM text.

    Tries in order: fenced ```json block → first {...} span → raw text.
    Raises ParsingError if nothing JSON-shaped is found.
    """
    if not text or not text.strip():
        raise ParsingError("Empty LLM response")

    fenced = _CODE_FENCE_PATTERN.search(text)
    if fenced:
        candidate = fenced.group(1).strip()
        if candidate:
            return candidate

    braced = _JSON_OBJECT_PATTERN.search(text)
    if braced:
        return braced.group(0).strip()

    stripped = text.strip().strip("`").strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        return stripped

    raise ParsingError(f"No JSON object found in response: {text[:200]!r}")


# -- Parsing --------------------------------------------------------------------


def parse_json(text: str) -> dict[str, Any]:
    """Extract + json.loads. Wraps JSONDecodeError in ParsingError with context."""
    raw_block = extract_json_block(clean_text(text))
    try:
        data = json.loads(raw_block)
    except json.JSONDecodeError as exc:
        logger.warning("parsing.json_decode_failed", error=str(exc), snippet=raw_block[:200])
        raise ParsingError(f"Invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ParsingError(f"Expected JSON object, got {type(data).__name__}")
    return data


def parse_model[T: BaseModel](text: str, model: type[T]) -> T:
    """Parse LLM text into a Pydantic model. Raises ParsingError on any failure."""
    data = parse_json(text)
    try:
        return model.model_validate(data)
    except ValidationError as exc:
        logger.warning("parsing.validation_failed", model=model.__name__, errors=exc.errors())
        raise ParsingError(f"LLM output did not match {model.__name__}: {exc}") from exc
