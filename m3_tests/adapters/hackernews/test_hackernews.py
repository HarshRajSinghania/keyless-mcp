"""Hacker News adapter: catalog, happy paths and error paths, replayed from cassettes."""

from __future__ import annotations

import pytest

from m3_tests._support.cassettes import recorded
from m3_tests._support.results import result_text

API = "https://hacker-news.firebaseio.com/v0"

pytestmark = pytest.mark.m3(suite_name="hackernews")


def test_lists_both_hackernews_tools_with_documented_inputs(connect) -> None:
    """The catalog has hackernews_top_stories(limit) and hackernews_get_item(item_id)."""
    with connect("hackernews") as client:
        tools = {t.name: t for t in client.list_all_tools() if t.name.startswith("hackernews_")}
    assert set(tools) == {"hackernews_top_stories", "hackernews_get_item"}
    top = tools["hackernews_top_stories"].input_schema
    assert "required" not in top or list(top["required"]) == []
    assert top["properties"]["limit"]["default"] == 10
    assert list(tools["hackernews_get_item"].input_schema["required"]) == ["item_id"]


def test_top_stories_returns_ranked_stories_with_discussion_links(connect, replaying) -> None:
    """Each story is ranked from 1, has a title, a score, an author and its HN page link."""
    with connect("hackernews") as client:
        result = client.call_tool("hackernews_top_stories", {"limit": 3})
    assert result.is_error is False, result_text(result)
    data = result.structured_content
    assert data["returned"] == len(data["stories"]) == 3
    assert [s["rank"] for s in data["stories"]] == [1, 2, 3]
    assert all(s["type"] in {"story", "job", "poll"} for s in data["stories"])
    assert len({s["id"] for s in data["stories"]}) == 3
    if replaying:
        # The front page moves every minute, so expect what the cassettes recorded, not literals.
        top_ids = recorded("hackernews", f"{API}/topstories.json")[:3]
        assert [s["id"] for s in data["stories"]] == top_ids
        for story in data["stories"]:
            item = recorded("hackernews", f"{API}/item/{story['id']}.json")
            assert story["title"] == item["title"]
            assert story["type"] == item["type"]
            assert story["score"] == item["score"]
            assert story["comments"] == item.get("descendants", 0)
            assert story["by"] == item["by"]
    for story in data["stories"]:
        assert story["title"]
        assert story["hn_url"] == f"https://news.ycombinator.com/item?id={story['id']}"
        assert isinstance(story["comments"], int) and story["comments"] >= 0
        assert story["time"].endswith("Z")
        assert story["url"] is None or story["url"].startswith("http")
        assert story["by"]


def test_get_item_returns_the_documented_dropbox_story(connect) -> None:
    """Item 8863 is dhouston's 'My YC app: Dropbox' story, the example in the HN API docs."""
    with connect("hackernews") as client:
        result = client.call_tool("hackernews_get_item", {"item_id": 8863})
    assert result.is_error is False, result_text(result)
    item = result.structured_content
    assert item["id"] == 8863
    assert item["type"] == "story"
    assert item["by"] == "dhouston"
    assert item["title"] == "My YC app: Dropbox - Throw away your USB drive"
    assert item["url"] == "http://www.getdropbox.com/u/2/screencast.html"
    assert item["comments"] >= 71
    assert item["time"] == "2007-04-04T19:16:40Z"
    assert item["reply_count"] > 10
    assert len(item["reply_ids"]) == 10
    assert item["hn_url"] == "https://news.ycombinator.com/item?id=8863"


def test_get_item_returns_a_comment_with_html_removed(connect) -> None:
    """Item 2921983 is Peter Norvig's comment; the <p> in its text becomes a space."""
    with connect("hackernews") as client:
        result = client.call_tool("hackernews_get_item", {"item_id": 2921983})
    assert result.is_error is False, result_text(result)
    item = result.structured_content
    assert item["type"] == "comment"
    assert item["by"] == "norvig"
    assert item["parent"] == 2921506
    assert item["title"] is None
    assert item["text"].startswith("Aw shucks, guys")
    assert "<p>" not in item["text"]
    assert "Tell you what" in item["text"]


def test_get_item_reports_an_id_that_does_not_exist(connect) -> None:
    """The API answers null for a missing id; it becomes a readable is_error result."""
    with connect("hackernews") as client:
        result = client.call_tool("hackernews_get_item", {"item_id": 999999999999})
    assert result.is_error is True
    assert "No Hacker News item with id 999999999999" in result_text(result)


@pytest.mark.parametrize(
    ("tool", "arguments", "message"),
    [
        ("hackernews_top_stories", {"limit": 0}, "limit must be between 1 and 30"),
        ("hackernews_top_stories", {"limit": 31}, "limit must be between 1 and 30"),
        ("hackernews_get_item", {"item_id": 0}, "item_id must be a positive integer"),
    ],
)
def test_invalid_input_is_rejected_before_any_request(connect, tool, arguments, message) -> None:
    """Out-of-range arguments are is_error results with a fix-it message; no cassette needed."""
    with connect("hackernews") as client:
        result = client.call_tool(tool, arguments)
    assert result.is_error is True
    assert message in result_text(result)


@pytest.mark.live
def test_live_top_stories_hits_the_real_api(connect) -> None:
    """Smoke test against the real Hacker News API (excluded from PR CI)."""
    with connect("hackernews", mode="live") as client:
        result = client.call_tool("hackernews_top_stories", {"limit": 2})
    assert result.is_error is False, result_text(result)
    assert result.structured_content["returned"] >= 1
