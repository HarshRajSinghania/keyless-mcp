"""arXiv adapter: catalog, happy paths and error paths, replayed from cassettes."""

from __future__ import annotations

import pytest

from m3_tests._support.results import result_text

pytestmark = pytest.mark.m3(suite_name="arxiv")

ATTENTION_PAPER = "1706.03762"


def test_lists_both_arxiv_tools_with_documented_inputs(connect) -> None:
    """The catalog has arxiv_search(query required) and arxiv_get_paper(arxiv_id required)."""
    with connect("arxiv") as client:
        tools = {t.name: t for t in client.list_all_tools() if t.name.startswith("arxiv_")}
    assert set(tools) == {"arxiv_search", "arxiv_get_paper"}
    assert list(tools["arxiv_search"].input_schema["required"]) == ["query"]
    assert set(tools["arxiv_search"].input_schema["properties"]) == {"query", "max_results"}
    assert list(tools["arxiv_get_paper"].input_schema["required"]) == ["arxiv_id"]


def test_search_returns_papers_with_the_documented_fields(connect) -> None:
    """A title search returns the Transformer paper with authors, abstract and PDF link."""
    with connect("arxiv") as client:
        result = client.call_tool(
            "arxiv_search", {"query": "ti:attention AND au:vaswani", "max_results": 3}
        )
    assert result.is_error is False, result_text(result)
    data = result.structured_content
    assert data["returned"] == len(data["papers"]) <= 3
    paper = next(p for p in data["papers"] if p["id"].startswith(ATTENTION_PAPER))
    assert paper["title"] == "Attention Is All You Need"
    assert "Ashish Vaswani" in paper["authors"]
    assert paper["published"].startswith("2017-06-12")
    assert paper["pdf_url"].startswith(f"https://arxiv.org/pdf/{ATTENTION_PAPER}")
    assert "Transformer" in paper["summary"]


def test_get_paper_returns_full_metadata(connect) -> None:
    """Fetching 1706.03762 returns its categories, a full abstract and its URL."""
    with connect("arxiv") as client:
        result = client.call_tool("arxiv_get_paper", {"arxiv_id": f"arXiv:{ATTENTION_PAPER}"})
    assert result.is_error is False, result_text(result)
    paper = result.structured_content
    assert paper["id"].startswith(ATTENTION_PAPER)
    assert paper["title"] == "Attention Is All You Need"
    assert paper["primary_category"] == "cs.CL"
    assert "cs.LG" in paper["categories"]
    assert paper["url"].startswith(f"https://arxiv.org/abs/{ATTENTION_PAPER}")
    assert len(paper["authors"]) == 8


def test_search_rejects_out_of_range_max_results(connect) -> None:
    """max_results=0 is an is_error result that states the allowed range, not a crash."""
    with connect("arxiv") as client:
        result = client.call_tool("arxiv_search", {"query": "graphs", "max_results": 0})
    assert result.is_error is True
    assert "between 1 and 25" in result_text(result)


def test_get_paper_rejects_a_malformed_id(connect) -> None:
    """A malformed id is rejected before any request, with an example of a valid one."""
    with connect("arxiv") as client:
        result = client.call_tool("arxiv_get_paper", {"arxiv_id": "not-an-id"})
    assert result.is_error is True
    assert "not a valid arXiv id" in result_text(result)


def test_get_paper_reports_an_unknown_id(connect) -> None:
    """A well-formed id that does not exist becomes a readable is_error result."""
    with connect("arxiv") as client:
        result = client.call_tool("arxiv_get_paper", {"arxiv_id": "9901.99999"})
    assert result.is_error is True
    assert "9901.99999" in result_text(result)


@pytest.mark.live
def test_live_search_hits_the_real_api(connect) -> None:
    """Smoke test against the real arXiv API (excluded from PR CI)."""
    with connect("arxiv", mode="live") as client:
        result = client.call_tool("arxiv_get_paper", {"arxiv_id": ATTENTION_PAPER})
    assert result.is_error is False, result_text(result)
    assert result.structured_content["title"] == "Attention Is All You Need"
