"""Hacker News tools. The official API returns ids first and one item per request, so the top
stories tool lists the ids and then fetches the items concurrently."""

import asyncio
from datetime import UTC, datetime
from typing import Annotated, Any

from pydantic import Field

from keyless_mcp.core import AdapterHttp, InvalidInput, ToolRegistry, strip_html, truncate

API_URL = "https://hacker-news.firebaseio.com/v0"
WEB_URL = "https://news.ycombinator.com/item?id="
MAX_STORIES = 30
MAX_KIDS = 10
TEXT_CHARS = 1500


def iso_time(unix_seconds: int | None) -> str | None:
    if unix_seconds is None:
        return None
    return datetime.fromtimestamp(unix_seconds, tz=UTC).isoformat().replace("+00:00", "Z")


def summarise_story(item: dict[str, Any], rank: int) -> dict[str, Any]:
    """Compact story record. Ask HN and job posts have no external URL, so ``url`` can be None;
    ``hn_url`` always points at the discussion page."""
    return {
        "rank": rank,
        "id": item["id"],
        "title": item.get("title"),
        "url": item.get("url"),
        "score": item.get("score"),
        "by": item.get("by"),
        "comments": item.get("descendants", 0),
        "type": item.get("type"),
        "time": iso_time(item.get("time")),
        "hn_url": f"{WEB_URL}{item['id']}",
    }


def register(tools: ToolRegistry, http: AdapterHttp) -> None:
    @tools.tool(title="Hacker News top stories")
    async def hackernews_top_stories(
        limit: Annotated[
            int,
            Field(
                description=f"How many top stories to return, 1 to {MAX_STORIES}. Default 10. "
                "The front page shows 30."
            ),
        ] = 10,
    ) -> dict[str, Any]:
        """Get the current top stories on Hacker News in front-page order, each with title,
        linked URL, score (points), author, number of comments, post time and the Hacker News
        discussion link. Use hackernews_get_item with an id to read a story's text or details."""
        if not 1 <= limit <= MAX_STORIES:
            raise InvalidInput(f"limit must be between 1 and {MAX_STORIES}.")
        ids = await http.get_json(f"{API_URL}/topstories.json")
        items = await asyncio.gather(
            *(http.get_json(f"{API_URL}/item/{story_id}.json") for story_id in ids[:limit])
        )
        stories = [
            summarise_story(item, rank)
            for rank, item in enumerate(items, start=1)
            if item and not item.get("deleted") and not item.get("dead")
        ]
        return {"returned": len(stories), "stories": stories}

    @tools.tool(title="Get Hacker News item")
    async def hackernews_get_item(
        item_id: Annotated[
            int,
            Field(
                description="Hacker News item id: the number after 'id=' in a news.ycombinator.com"
                "/item?id=... link, e.g. 8863 (a story) or 2921983 (a comment). Positive integer."
            ),
        ],
    ) -> dict[str, Any]:
        """Get one Hacker News item by id: a story, comment, job, poll or poll option. Returns
        its type, title, text (HTML removed), link, author, score, post time, parent id (for
        comments), comment count and the ids of its first replies."""
        if item_id < 1:
            raise InvalidInput("item_id must be a positive integer, e.g. 8863.")
        item = await http.get_json(f"{API_URL}/item/{item_id}.json")
        if not item:  # the API answers null for ids that do not exist
            raise InvalidInput(
                f"No Hacker News item with id {item_id}. Ids are the number after 'id=' in "
                "news.ycombinator.com links; use hackernews_top_stories to find current ones."
            )
        kids = item.get("kids") or []
        return {
            "id": item["id"],
            "type": item.get("type"),
            "title": item.get("title"),
            "text": truncate(strip_html(item.get("text")), TEXT_CHARS) or None,
            "url": item.get("url"),
            "by": item.get("by"),
            "score": item.get("score"),
            "time": iso_time(item.get("time")),
            "parent": item.get("parent"),
            "comments": item.get("descendants"),
            "reply_count": len(kids),
            "reply_ids": kids[:MAX_KIDS],
            "deleted": bool(item.get("deleted")),
            "dead": bool(item.get("dead")),
            "hn_url": f"{WEB_URL}{item['id']}",
        }
