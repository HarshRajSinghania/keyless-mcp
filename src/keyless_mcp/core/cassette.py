"""Cassettes: one human-readable JSON file per upstream HTTP request.

A cassette is keyed by a stable hash of (method, URL with sorted query params, body). Request
headers are never stored. The filename carries a readable prefix (method, host, path) plus the
hash, so ``git diff`` and ``ls`` stay meaningful and lookup is a direct path computation.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


@dataclass(frozen=True)
class RecordedResponse:
    """The parts of an HTTP response a cassette preserves."""

    status: int
    content_type: str
    body: Any  # parsed JSON when the body was JSON, otherwise the text (str)


def canonical_url(url: str, params: dict[str, Any] | None = None) -> str:
    """Return ``url`` with ``params`` merged in and all query parameters sorted."""
    parts = urlsplit(url)
    pairs = parse_qsl(parts.query, keep_blank_values=True)
    pairs.extend((k, str(v)) for k, v in (params or {}).items() if v is not None)
    query = urlencode(sorted(pairs))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, query, ""))


def canonical_body(body: Any) -> str | None:
    """Stable text form of a request body (``None`` when there is no body)."""
    if body is None:
        return None
    if isinstance(body, bytes):
        body = body.decode("utf-8", errors="replace")
    if isinstance(body, str):
        return body
    return json.dumps(body, sort_keys=True, separators=(",", ":"))


def request_key(method: str, url: str, body: Any = None) -> str:
    """Stable 12 hex character hash of a request."""
    material = json.dumps([method.upper(), url, canonical_body(body)])
    return hashlib.sha256(material.encode()).hexdigest()[:12]


def _slug(text: str, limit: int) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()[:limit] or "root"


def cassette_path(directory: Path, method: str, url: str, body: Any = None) -> Path:
    parts = urlsplit(url)
    name = f"{method.lower()}_{_slug(parts.netloc, 30)}_{_slug(parts.path, 40)}"
    return directory / f"{name}_{request_key(method, url, body)}.json"


def save(directory: Path, method: str, url: str, body: Any, response: RecordedResponse) -> Path:
    """Write the cassette for one request/response pair and return its path."""
    path = cassette_path(directory, method, url, body)
    path.parent.mkdir(parents=True, exist_ok=True)
    document = {
        "request": {"method": method.upper(), "url": url, "body": _jsonable(body)},
        "response": {
            "status": response.status,
            "content_type": response.content_type,
            **_encode_body(response.body),
        },
    }
    path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def load(directory: Path, method: str, url: str, body: Any = None) -> RecordedResponse | None:
    """Return the recorded response for a request, or ``None`` when no cassette matches."""
    path = cassette_path(directory, method, url, body)
    if not path.is_file():
        return None
    response = json.loads(path.read_text(encoding="utf-8"))["response"]
    return RecordedResponse(
        status=response["status"],
        content_type=response["content_type"],
        body=_decode_body(response),
    )


def _encode_body(body: Any) -> dict[str, Any]:
    """JSON bodies are stored as JSON; text bodies as a list of lines so diffs stay line-based."""
    if isinstance(body, str):
        return {"body_format": "text", "body": body.splitlines(keepends=True)}
    return {"body_format": "json", "body": _sort_keys(body)}


def _sort_keys(value: Any) -> Any:
    """Sort object keys recursively: some APIs reorder them per request, which would make every
    re-record a noisy diff. List order is data and is left alone."""
    if isinstance(value, dict):
        return {key: _sort_keys(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [_sort_keys(item) for item in value]
    return value


def _decode_body(response: dict[str, Any]) -> Any:
    if response["body_format"] == "text":
        return "".join(response["body"])
    return response["body"]


def _jsonable(body: Any) -> Any:
    if isinstance(body, bytes):
        return body.decode("utf-8", errors="replace")
    return body
