"""Wikipedia adapter: catalog, happy paths and error paths, replayed from cassettes."""

from __future__ import annotations

import pytest

from m3_tests._support.results import result_text

pytestmark = pytest.mark.m3(suite_name="wikipedia")


def test_lists_both_wikipedia_tools_with_documented_inputs(connect) -> None:
    """The catalog has wikipedia_search(query) and wikipedia_get_summary(title)."""
    with connect("wikipedia") as client:
        tools = {t.name: t for t in client.list_all_tools() if t.name.startswith("wikipedia_")}
    assert set(tools) == {"wikipedia_search", "wikipedia_get_summary"}
    search, summary = tools["wikipedia_search"], tools["wikipedia_get_summary"]
    assert list(search.input_schema["required"]) == ["query"]
    assert set(search.input_schema["properties"]) == {"query", "limit", "lang"}
    assert search.input_schema["properties"]["lang"]["default"] == "en"
    assert search.input_schema["properties"]["limit"]["default"] == 5
    assert list(summary.input_schema["required"]) == ["title"]
    assert set(summary.input_schema["properties"]) == {"title", "lang"}


def test_search_finds_the_alan_turing_article(connect) -> None:
    """Searching for a person's full name returns that person's article first, with a link."""
    with connect("wikipedia") as client:
        result = client.call_tool("wikipedia_search", {"query": "alan turing", "limit": 3})
    assert result.is_error is False, result_text(result)
    data = result.structured_content
    assert data["lang"] == "en"
    assert data["returned"] == len(data["results"]) == 3
    top = data["results"][0]
    assert top["title"] == "Alan Turing"
    assert top["url"] == "https://en.wikipedia.org/wiki/Alan_Turing"
    assert "Turing" in top["excerpt"]
    assert "<" not in top["excerpt"], "highlight markup must be stripped from excerpts"
    assert "computer scientist" in top["description"].lower()


def test_search_uses_the_requested_language_edition(connect) -> None:
    """lang='de' searches German Wikipedia and links to de.wikipedia.org."""
    with connect("wikipedia") as client:
        result = client.call_tool("wikipedia_search", {"query": "berlin", "limit": 2, "lang": "de"})
    assert result.is_error is False, result_text(result)
    data = result.structured_content
    assert data["lang"] == "de"
    assert data["results"][0]["title"] == "Berlin"
    assert data["results"][0]["url"] == "https://de.wikipedia.org/wiki/Berlin"
    assert "Hauptstadt" in data["results"][0]["excerpt"]


def test_summary_returns_the_article_intro(connect) -> None:
    """The Alan Turing summary describes him as a mathematician and links to the article."""
    with connect("wikipedia") as client:
        result = client.call_tool("wikipedia_get_summary", {"title": "Alan Turing"})
    assert result.is_error is False, result_text(result)
    data = result.structured_content
    assert data["title"] == "Alan Turing"
    assert "mathematician" in data["summary"]
    assert "Turing" in data["summary"]
    assert data["is_disambiguation"] is False
    assert data["url"] == "https://en.wikipedia.org/wiki/Alan_Turing"
    assert data["last_modified"]


def test_summary_in_another_language(connect) -> None:
    """Paris in French Wikipedia is described in French as the capital of France."""
    with connect("wikipedia") as client:
        result = client.call_tool("wikipedia_get_summary", {"title": "Paris", "lang": "fr"})
    assert result.is_error is False, result_text(result)
    data = result.structured_content
    assert data["lang"] == "fr"
    assert "capitale de la France" in data["summary"]
    assert data["url"] == "https://fr.wikipedia.org/wiki/Paris"


def test_summary_flags_disambiguation_pages(connect) -> None:
    """'Mercury' is a disambiguation page listing several meanings."""
    with connect("wikipedia") as client:
        result = client.call_tool("wikipedia_get_summary", {"title": "Mercury"})
    assert result.is_error is False, result_text(result)
    data = result.structured_content
    assert data["is_disambiguation"] is True
    assert "Mercury" in data["summary"]


def test_summary_of_a_missing_article_points_to_search(connect) -> None:
    """The API's HTTP 404 becomes a readable is_error result naming the title."""
    with connect("wikipedia") as client:
        result = client.call_tool("wikipedia_get_summary", {"title": "Zzzxqnotapage123"})
    assert result.is_error is True
    text = result_text(result)
    assert "No en.wikipedia.org article titled 'Zzzxqnotapage123'" in text
    assert "wikipedia_search" in text


@pytest.mark.parametrize(
    ("tool", "arguments", "message"),
    [
        ("wikipedia_search", {"query": "  "}, "query must not be empty"),
        ("wikipedia_search", {"query": "x", "limit": 0}, "limit must be between 1 and 20"),
        ("wikipedia_search", {"query": "x", "lang": "evil.com/"}, "not a Wikipedia language code"),
        ("wikipedia_get_summary", {"title": ""}, "title must not be empty"),
        ("wikipedia_get_summary", {"title": "x", "lang": "EN US"}, "not a Wikipedia language code"),
    ],
)
def test_invalid_input_is_rejected_before_any_request(connect, tool, arguments, message) -> None:
    """Bad arguments are is_error results with a fix-it message; no cassette is needed."""
    with connect("wikipedia") as client:
        result = client.call_tool(tool, arguments)
    assert result.is_error is True
    assert message in result_text(result)


@pytest.mark.live
def test_live_summary_hits_the_real_api(connect) -> None:
    """Smoke test against the real Wikipedia API (excluded from PR CI)."""
    with connect("wikipedia", mode="live") as client:
        result = client.call_tool("wikipedia_get_summary", {"title": "Alan Turing"})
    assert result.is_error is False, result_text(result)
    assert result.structured_content["title"] == "Alan Turing"
