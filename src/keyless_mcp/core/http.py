"""The one shared HTTP client every adapter uses.

Adapters never import httpx. They call :class:`AdapterHttp` (``get_json``, ``get_text``,
``post_json``), which gives them the User-Agent, timeouts, per-adapter rate limiting, offline
record/replay and mapping of every upstream failure to a readable ``UpstreamError``.

Modes (env ``KEYLESS_MCP_HTTP_MODE``):

* ``live`` (default): talk to the real API.
* ``record``: talk to the real API and write one cassette per request to
  ``KEYLESS_MCP_CASSETTE_DIR``.
* ``replay``: never touch the network; answer from cassettes, fail loudly on a miss.
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

import httpx

from keyless_mcp import USER_AGENT

from . import cassette
from .errors import CassetteMiss, UpstreamError
from .ratelimit import RateLimiter

MODE_ENV = "KEYLESS_MCP_HTTP_MODE"
CASSETTE_DIR_ENV = "KEYLESS_MCP_CASSETTE_DIR"


class HttpMode(StrEnum):
    LIVE = "live"
    RECORD = "record"
    REPLAY = "replay"


@dataclass(frozen=True)
class HttpConfig:
    mode: HttpMode = HttpMode.LIVE
    cassette_dir: Path | None = None
    timeout: float = 20.0

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> HttpConfig:
        env = os.environ if env is None else env
        raw_mode = (env.get(MODE_ENV) or "live").strip().lower()
        try:
            mode = HttpMode(raw_mode)
        except ValueError:
            valid = ", ".join(m.value for m in HttpMode)
            raise ValueError(f"{MODE_ENV}={raw_mode!r} is not valid; use one of: {valid}") from None
        raw_dir = env.get(CASSETTE_DIR_ENV)
        return cls(mode=mode, cassette_dir=Path(raw_dir) if raw_dir else None)


class HttpClient:
    """Shared client. Create one per server process and hand out per-adapter views."""

    def __init__(
        self, config: HttpConfig | None = None, *, transport: httpx.AsyncBaseTransport | None = None
    ) -> None:
        self.config = config or HttpConfig()
        self._transport = transport
        self._client: httpx.AsyncClient | None = None

    def for_adapter(self, name: str, rate_limit_per_minute: int) -> AdapterHttp:
        return AdapterHttp(self, name, RateLimiter(rate_limit_per_minute))

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    def _live_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers={"User-Agent": USER_AGENT},
                timeout=httpx.Timeout(self.config.timeout, connect=10.0),
                follow_redirects=True,
                transport=self._transport,
            )
        return self._client

    def _require_cassette_dir(self) -> Path:
        directory = self.config.cassette_dir
        if directory is None:
            raise UpstreamError(
                f"{MODE_ENV}={self.config.mode.value} needs {CASSETTE_DIR_ENV} "
                "to point at a cassette directory."
            )
        return directory

    async def fetch(
        self,
        adapter: AdapterHttp,
        method: str,
        url: str,
        params: Mapping[str, Any] | None,
        json_body: Any,
    ) -> cassette.RecordedResponse:
        """Perform (or replay) one request and return the response. Raises on HTTP errors."""
        url = cassette.canonical_url(url, dict(params) if params else None)
        if self.config.mode is HttpMode.REPLAY:
            response = self._replay(adapter.name, method, url, json_body)
        else:
            response = await self._send(adapter, method, url, json_body)
            if self.config.mode is HttpMode.RECORD:
                cassette.save(self._require_cassette_dir(), method, url, json_body, response)
        if response.status >= 400:
            raise UpstreamError(
                f"{adapter.name}: {method} {url} returned HTTP {response.status}: "
                f"{_snippet(response.body)}",
                status=response.status,
            )
        return response

    def _replay(self, adapter: str, method: str, url: str, body: Any) -> cassette.RecordedResponse:
        directory = self._require_cassette_dir()
        recorded = cassette.load(directory, method, url, body)
        if recorded is None:
            expected = cassette.cassette_path(directory, method, url, body).name
            raise CassetteMiss(
                f"{adapter}: no cassette for {method} {url} in {directory} (expected {expected}). "
                f"Replay mode never uses the network. Record it with {MODE_ENV}=record "
                f"{CASSETTE_DIR_ENV}={directory} (or `make record ADAPTER={adapter}`)."
            )
        return recorded

    async def _send(
        self, adapter: AdapterHttp, method: str, url: str, json_body: Any
    ) -> cassette.RecordedResponse:
        await adapter.limiter.acquire()
        try:
            raw = await self._live_client().request(method, url, json=json_body)
        except httpx.TimeoutException:
            raise UpstreamError(
                f"{adapter.name}: {method} {url} timed out after {self.config.timeout:g}s. "
                "The upstream API is slow or unavailable; try again shortly."
            ) from None
        except httpx.HTTPError as exc:
            raise UpstreamError(
                f"{adapter.name}: could not reach {url} ({type(exc).__name__}: {exc}). "
                "Check the network connection or try again shortly."
            ) from None
        content_type = raw.headers.get("content-type", "").split(";")[0].strip().lower()
        text = raw.text
        body: Any = text
        if "json" in content_type:
            try:
                body = json.loads(text)
            except ValueError:
                body = text
        return cassette.RecordedResponse(raw.status_code, content_type, body)


@dataclass
class AdapterHttp:
    """The HTTP handle an adapter receives: rate-limited and bound to the adapter's name."""

    client: HttpClient
    name: str
    limiter: RateLimiter

    async def get_json(self, url: str, params: Mapping[str, Any] | None = None) -> Any:
        response = await self.client.fetch(self, "GET", url, params, None)
        return self._require_json(url, response)

    async def post_json(
        self, url: str, json_body: Any, params: Mapping[str, Any] | None = None
    ) -> Any:
        response = await self.client.fetch(self, "POST", url, params, json_body)
        return self._require_json(url, response)

    async def get_text(self, url: str, params: Mapping[str, Any] | None = None) -> str:
        response = await self.client.fetch(self, "GET", url, params, None)
        body = response.body
        return body if isinstance(body, str) else json.dumps(body)

    def _require_json(self, url: str, response: cassette.RecordedResponse) -> Any:
        if isinstance(response.body, str):
            raise UpstreamError(
                f"{self.name}: {url} did not return valid JSON "
                f"(content-type {response.content_type or 'unknown'}): {_snippet(response.body)}"
            )
        return response.body


def _snippet(body: Any, limit: int = 200) -> str:
    text = body if isinstance(body, str) else json.dumps(body, ensure_ascii=False)
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"
