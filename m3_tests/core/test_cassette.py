"""The cassette layer: stable keys, readable files, lossless round trips."""

from __future__ import annotations

import json

import pytest

from keyless_mcp.core import cassette

pytestmark = pytest.mark.m3(suite_name="core")


def test_url_is_canonicalised_with_sorted_query_params() -> None:
    """Parameter order never changes the cassette key."""
    a = cassette.canonical_url("https://x.test/p?b=2&a=1")
    b = cassette.canonical_url("https://x.test/p", {"a": 1, "b": 2})
    assert a == b == "https://x.test/p?a=1&b=2"


def test_none_params_are_dropped() -> None:
    assert (
        cassette.canonical_url("https://x.test/p", {"a": None, "b": "1"}) == "https://x.test/p?b=1"
    )


def test_key_depends_on_method_url_and_body_only() -> None:
    url = "https://x.test/p?a=1"
    base = cassette.request_key("POST", url, {"k": 1, "j": 2})
    assert base == cassette.request_key("post", url, {"j": 2, "k": 1}), (
        "key order and case are ignored"
    )
    assert base != cassette.request_key("GET", url, {"k": 1, "j": 2})
    assert base != cassette.request_key("POST", url + "&b=2", {"k": 1, "j": 2})
    assert base != cassette.request_key("POST", url, {"k": 2, "j": 2})
    assert len(base) == 12


def test_json_response_round_trips_and_file_is_readable(tmp_path) -> None:
    """The cassette is indented JSON with the request, status and content type, and no headers."""
    url = "https://api.test/v1/items?id=7"
    response = cassette.RecordedResponse(200, "application/json", {"id": 7, "tags": ["a", "b"]})
    path = cassette.save(tmp_path, "GET", url, None, response)
    assert path.name.startswith("get_api-test_v1-items_")
    document = json.loads(path.read_text())
    assert document["request"] == {"method": "GET", "url": url, "body": None}
    assert document["response"]["status"] == 200
    assert document["response"]["body"] == {"id": 7, "tags": ["a", "b"]}
    assert "headers" not in document["request"] and "headers" not in document["response"]
    assert "\n  " in path.read_text(), "indented for diffs"
    assert cassette.load(tmp_path, "GET", url, None) == response


def test_text_response_is_stored_line_by_line_and_restored_exactly(tmp_path) -> None:
    text = "<?xml version='1.0'?>\n<a>\n  <b/>\n</a>\n"
    url = "https://api.test/feed"
    response = cassette.RecordedResponse(200, "application/atom+xml", text)
    path = cassette.save(tmp_path, "GET", url, None, response)
    assert json.loads(path.read_text())["response"]["body"] == text.splitlines(keepends=True)
    assert cassette.load(tmp_path, "GET", url, None).body == text


def test_post_body_is_part_of_the_key(tmp_path) -> None:
    url = "https://api.test/query"
    cassette.save(
        tmp_path,
        "POST",
        url,
        {"q": 1},
        cassette.RecordedResponse(200, "application/json", {"r": 1}),
    )
    assert cassette.load(tmp_path, "POST", url, {"q": 1}).body == {"r": 1}
    assert cassette.load(tmp_path, "POST", url, {"q": 2}) is None


def test_load_returns_none_for_a_missing_cassette_or_directory(tmp_path) -> None:
    assert cassette.load(tmp_path, "GET", "https://api.test/none") is None
    assert cassette.load(tmp_path / "missing", "GET", "https://api.test/none") is None


def test_object_keys_are_sorted_so_rerecords_do_not_produce_noisy_diffs(tmp_path) -> None:
    url = "https://api.test/v1/x"
    body = {"b": 1, "a": {"z": 1, "y": [{"q": 1, "p": 2}]}}
    path = cassette.save(
        tmp_path, "GET", url, None, cassette.RecordedResponse(200, "application/json", body)
    )
    stored = json.loads(path.read_text())["response"]["body"]
    assert list(stored) == ["a", "b"]
    assert list(stored["a"]) == ["y", "z"]
    assert list(stored["a"]["y"][0]) == ["p", "q"]
    assert cassette.load(tmp_path, "GET", url, None).body == body


def test_emails_are_redacted_everywhere_in_a_stored_cassette(tmp_path) -> None:
    """Maintainer contacts in a registry response never reach disk, in JSON or text bodies."""
    url = "https://registry.test/pkg"
    body = {
        "author": {"name": "Ada", "email": "ada.lovelace+npm@example.org"},
        "maintainers": ["Bob <bob@corp.example.com>", "plain text"],
        "nested": [{"contact": "mailto:carol@sub.domain.io?subject=hi"}],
    }
    path = cassette.save(
        tmp_path, "GET", url, None, cassette.RecordedResponse(200, "application/json", body)
    )
    raw = path.read_text()
    assert not any(e in raw for e in ("ada.lovelace", "bob@", "carol@")), raw
    stored = json.loads(raw)["response"]["body"]
    assert stored["author"] == {"name": "Ada", "email": "redacted@example.invalid"}
    assert stored["maintainers"] == ["Bob <redacted@example.invalid>", "plain text"]
    assert stored["nested"][0]["contact"] == "mailto:redacted@example.invalid?subject=hi"
    # The key came from the real request, so replay still finds the (redacted) cassette.
    assert cassette.load(tmp_path, "GET", url, None).body["author"]["name"] == "Ada"

    text_path = cassette.save(
        tmp_path,
        "GET",
        "https://registry.test/feed",
        None,
        cassette.RecordedResponse(200, "text/plain", "line one\nwrite to me@host.test now\n"),
    )
    assert "me@host.test" not in text_path.read_text()
    assert cassette.load(tmp_path, "GET", "https://registry.test/feed").body == (
        "line one\nwrite to redacted@example.invalid now\n"
    )


def test_redaction_keeps_structure_is_idempotent_and_leaves_keys_alone() -> None:
    value = {"a@b.co": ["x@y.io", 3, None, {"k": "no email here"}]}
    once = cassette.redact_emails(value)
    assert once == {"a@b.co": ["redacted@example.invalid", 3, None, {"k": "no email here"}]}
    assert cassette.redact_emails(once) == once


def test_the_generic_git_ssh_user_is_dropped_so_repository_urls_still_parse() -> None:
    """`git@github.com` is not a person; it is rewritten so a URL stays a URL."""
    assert (
        cassette.redact_emails("git+ssh://git@github.com/o/r.git") == "git+ssh://github.com/o/r.git"
    )
    assert cassette.redact_emails("git@github.com:o/r.git") == "ssh://github.com/o/r.git"
