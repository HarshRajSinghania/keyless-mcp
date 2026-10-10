"""The shared HTTP client: modes, offline guarantee and upstream error mapping."""

from __future__ import annotations

from pathlib import Path

import anyio
import httpx
import pytest

from keyless_mcp import USER_AGENT
from keyless_mcp.core import (
    CassetteMiss,
    HttpClient,
    HttpConfig,
    HttpMode,
    UpstreamError,
)
from keyless_mcp.core.ratelimit import RateLimiter

pytestmark = pytest.mark.m3(suite_name="core")

URL = "https://api.test/v1/thing"


def client_with(handler, mode: HttpMode, cassette_dir: Path | None = None) -> HttpClient:
    config = HttpConfig(mode=mode, cassette_dir=cassette_dir, timeout=5)
    return HttpClient(config, transport=httpx.MockTransport(handler))


def run(coro_fn):
    return anyio.run(coro_fn)


def test_user_agent_identifies_keyless_mcp() -> None:
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["ua"] = request.headers["user-agent"]
        return httpx.Response(200, json={"ok": True})

    api = client_with(handler, HttpMode.LIVE).for_adapter("demo", 600)
    assert run(lambda: api.get_json(URL)) == {"ok": True}
    assert seen["ua"] == USER_AGENT
    assert seen["ua"].startswith("keyless-mcp/")
    assert seen["ua"].endswith("(+https://github.com/sineframe/keyless-mcp)")


def test_params_are_sorted_into_the_request_url() -> None:
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        return httpx.Response(200, json={})

    api = client_with(handler, HttpMode.LIVE).for_adapter("demo", 600)
    run(lambda: api.get_json(URL, {"b": 2, "a": 1}))
    assert seen["url"] == f"{URL}?a=1&b=2"


def test_record_then_replay_returns_the_same_data_without_the_network(tmp_path) -> None:
    calls = []

    def live(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, json={"answer": 42})

    def forbidden(request: httpx.Request) -> httpx.Response:
        raise AssertionError("replay mode must not touch the network")

    recorder = client_with(live, HttpMode.RECORD, tmp_path).for_adapter("demo", 600)
    assert run(lambda: recorder.get_json(URL, {"q": "x"})) == {"answer": 42}
    assert len(calls) == 1
    assert len(list(tmp_path.glob("*.json"))) == 1

    replayer = client_with(forbidden, HttpMode.REPLAY, tmp_path).for_adapter("demo", 600)
    assert run(lambda: replayer.get_json(URL, {"q": "x"})) == {"answer": 42}


def test_replay_miss_names_the_request_and_how_to_record_it(tmp_path) -> None:
    api = client_with(lambda r: httpx.Response(500), HttpMode.REPLAY, tmp_path).for_adapter(
        "demo", 600
    )
    with pytest.raises(CassetteMiss) as caught:
        run(lambda: api.get_json(URL, {"q": "x"}))
    message = str(caught.value)
    assert f"GET {URL}?q=x" in message
    assert "KEYLESS_MCP_HTTP_MODE=record" in message
    assert str(tmp_path) in message
    assert "make record ADAPTER=demo" in message


def test_replay_and_record_require_a_cassette_directory() -> None:
    for mode in (HttpMode.REPLAY, HttpMode.RECORD):
        api = client_with(lambda r: httpx.Response(200, json={}), mode).for_adapter("demo", 600)
        with pytest.raises(UpstreamError, match="KEYLESS_MCP_CASSETTE_DIR"):
            run(lambda api=api: api.get_json(URL))


@pytest.mark.parametrize("status", [404, 500, 503])
def test_http_errors_become_upstream_errors_with_the_status(status) -> None:
    api = client_with(
        lambda r: httpx.Response(status, json={"message": "nope"}), HttpMode.LIVE
    ).for_adapter("demo", 600)
    with pytest.raises(UpstreamError) as caught:
        run(lambda: api.get_json(URL))
    assert caught.value.status == status
    assert f"HTTP {status}" in str(caught.value)
    assert "nope" in str(caught.value)


def test_error_responses_are_recorded_so_error_paths_can_be_replayed(tmp_path) -> None:
    recorder = client_with(lambda r: httpx.Response(404, json={"m": 1}), HttpMode.RECORD, tmp_path)
    with pytest.raises(UpstreamError):
        run(lambda: recorder.for_adapter("demo", 600).get_json(URL))
    replayer = client_with(lambda r: httpx.Response(200), HttpMode.REPLAY, tmp_path)
    with pytest.raises(UpstreamError) as caught:
        run(lambda: replayer.for_adapter("demo", 600).get_json(URL))
    assert caught.value.status == 404


def test_timeout_becomes_a_readable_upstream_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow", request=request)

    api = client_with(handler, HttpMode.LIVE).for_adapter("demo", 600)
    with pytest.raises(UpstreamError, match="timed out after 5s"):
        run(lambda: api.get_json(URL))


def test_connection_failure_becomes_a_readable_upstream_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("dns failure", request=request)

    api = client_with(handler, HttpMode.LIVE).for_adapter("demo", 600)
    with pytest.raises(UpstreamError, match="could not reach"):
        run(lambda: api.get_json(URL))


def test_invalid_json_becomes_a_readable_upstream_error() -> None:
    api = client_with(
        lambda r: httpx.Response(
            200, text="<html>oops</html>", headers={"content-type": "application/json"}
        ),
        HttpMode.LIVE,
    ).for_adapter("demo", 600)
    with pytest.raises(UpstreamError, match="did not return valid JSON"):
        run(lambda: api.get_json(URL))


def test_get_text_returns_the_raw_body() -> None:
    api = client_with(
        lambda r: httpx.Response(200, text="<a/>", headers={"content-type": "application/xml"}),
        HttpMode.LIVE,
    ).for_adapter("demo", 600)
    assert run(lambda: api.get_text(URL)) == "<a/>"


def test_config_reads_mode_and_cassette_dir_from_env() -> None:
    config = HttpConfig.from_env(
        {"KEYLESS_MCP_HTTP_MODE": "Replay", "KEYLESS_MCP_CASSETTE_DIR": "/tmp/c"}
    )
    assert config.mode is HttpMode.REPLAY
    assert config.cassette_dir == Path("/tmp/c")
    assert HttpConfig.from_env({}).mode is HttpMode.LIVE


def test_config_rejects_an_unknown_mode() -> None:
    with pytest.raises(ValueError, match="live, record, replay"):
        HttpConfig.from_env({"KEYLESS_MCP_HTTP_MODE": "offline"})


def test_rate_limiter_spaces_calls_by_sixty_over_the_limit() -> None:
    now = [0.0]
    slept: list[float] = []

    async def sleep(seconds: float) -> None:
        slept.append(seconds)
        now[0] += seconds

    limiter = RateLimiter(20, clock=lambda: now[0], sleep=sleep)  # one call per 3 seconds

    async def three_calls() -> None:
        for _ in range(3):
            await limiter.acquire()

    run(three_calls)
    assert slept == [3.0, 3.0]


def test_rate_limiter_does_not_wait_when_calls_are_already_spread_out() -> None:
    now = [0.0]
    slept: list[float] = []

    async def sleep(seconds: float) -> None:
        slept.append(seconds)

    limiter = RateLimiter(60, clock=lambda: now[0], sleep=sleep)

    async def spaced() -> None:
        await limiter.acquire()
        now[0] = 10.0
        await limiter.acquire()

    run(spaced)
    assert slept == []
