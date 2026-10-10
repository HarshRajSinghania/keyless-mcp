"""arXiv tools. The API returns Atom XML, parsed here with the standard library."""

import re
import xml.etree.ElementTree as ET
from typing import Annotated, Any

from pydantic import Field

from keyless_mcp.core import AdapterHttp, InvalidInput, ToolRegistry, UpstreamError, tidy, truncate

API_URL = "https://export.arxiv.org/api/query"
ATOM = "{http://www.w3.org/2005/Atom}"
OPENSEARCH = "{http://a9.com/-/spec/opensearch/1.1/}"
ARXIV = "{http://arxiv.org/schemas/atom}"

MAX_RESULTS_LIMIT = 25
SEARCH_SUMMARY_CHARS = 600
PAPER_SUMMARY_CHARS = 3000

# New style (2301.12345, 2301.12345v2) or old style (hep-th/9901001, math.GT/0309136v1).
ARXIV_ID_RE = re.compile(r"^(\d{4}\.\d{4,5}|[a-z\-]+(\.[A-Z]{2})?/\d{7})(v\d+)?$")
FIELD_PREFIX_RE = re.compile(r"\b(all|ti|au|abs|co|jr|cat|rn|id):")


def build_search_query(query: str) -> str:
    """Plain words become ``all:a AND all:b``; queries using arXiv field prefixes pass through."""
    if FIELD_PREFIX_RE.search(query):
        return query
    return " AND ".join(f"all:{word}" for word in query.split())


def normalise_arxiv_id(raw: str) -> str:
    """Accept ``2301.12345``, ``arXiv:2301.12345v2`` or an arxiv.org/abs URL."""
    text = raw.strip()
    text = re.sub(r"^https?://arxiv\.org/(abs|pdf)/", "", text)
    text = re.sub(r"^arxiv:", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\.pdf$", "", text)
    if not ARXIV_ID_RE.match(text):
        raise InvalidInput(
            f"{raw!r} is not a valid arXiv id. Use a form like '1706.03762', '2301.12345v2' "
            "or 'hep-th/9901001'."
        )
    return text


def _text(entry: ET.Element, tag: str) -> str:
    node = entry.find(tag)
    return tidy(node.text) if node is not None else ""


def parse_feed(xml_text: str) -> tuple[int, list[ET.Element]]:
    """Return (total results, entries) from an Atom response; raise on arXiv's error entries."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise UpstreamError(f"arxiv: response was not valid Atom XML ({exc})") from exc
    entries = root.findall(f"{ATOM}entry")
    for entry in entries:
        if "/api/errors" in _text(entry, f"{ATOM}id"):
            raise InvalidInput(f"arXiv rejected the request: {_text(entry, f'{ATOM}summary')}")
    total_text = _text(root, f"{OPENSEARCH}totalResults")
    total = int(total_text) if total_text.isdigit() else len(entries)
    return total, entries


def entry_to_paper(entry: ET.Element, *, summary_chars: int, detailed: bool) -> dict[str, Any]:
    abs_url = _text(entry, f"{ATOM}id").replace("http://", "https://", 1)
    arxiv_id = abs_url.split("/abs/", 1)[-1]
    pdf_url = next(
        (
            link.get("href", "")
            for link in entry.findall(f"{ATOM}link")
            if link.get("title") == "pdf"
        ),
        f"https://arxiv.org/pdf/{arxiv_id}",
    )
    paper: dict[str, Any] = {
        "id": arxiv_id,
        "title": _text(entry, f"{ATOM}title"),
        "authors": [_text(a, f"{ATOM}name") for a in entry.findall(f"{ATOM}author")],
        "summary": truncate(_text(entry, f"{ATOM}summary"), summary_chars),
        "published": _text(entry, f"{ATOM}published"),
        "pdf_url": pdf_url.replace("http://", "https://", 1),
        "url": abs_url,
    }
    if detailed:
        primary = entry.find(f"{ARXIV}primary_category")
        paper.update(
            {
                "updated": _text(entry, f"{ATOM}updated"),
                "primary_category": primary.get("term", "") if primary is not None else "",
                "categories": [c.get("term", "") for c in entry.findall(f"{ATOM}category")],
                "doi": _text(entry, f"{ARXIV}doi") or None,
                "journal_ref": _text(entry, f"{ARXIV}journal_ref") or None,
                "comment": _text(entry, f"{ARXIV}comment") or None,
            }
        )
    return paper


def register(tools: ToolRegistry, http: AdapterHttp) -> None:
    @tools.tool(title="Search arXiv")
    async def arxiv_search(
        query: Annotated[
            str,
            Field(
                description="Search terms, e.g. 'graph neural networks'. Plain words are matched "
                "across all fields. Advanced: use arXiv field prefixes ti: (title), au: (author), "
                "abs: (abstract), cat: (category), combined with AND/OR, "
                "e.g. 'au:hinton AND cat:cs.LG'."
            ),
        ],
        max_results: Annotated[
            int,
            Field(description=f"How many papers to return, 1 to {MAX_RESULTS_LIMIT}. Default 5."),
        ] = 5,
    ) -> dict[str, Any]:
        """Search arXiv preprints. Returns matching papers with title, authors, a trimmed
        abstract, publication date, PDF link and arXiv id, most relevant first."""
        if not query.strip():
            raise InvalidInput("query must not be empty.")
        if not 1 <= max_results <= MAX_RESULTS_LIMIT:
            raise InvalidInput(f"max_results must be between 1 and {MAX_RESULTS_LIMIT}.")
        xml_text = await http.get_text(
            API_URL,
            {"search_query": build_search_query(query), "start": 0, "max_results": max_results},
        )
        total, entries = parse_feed(xml_text)
        return {
            "query": query,
            "total_results": total,
            "returned": len(entries),
            "papers": [
                entry_to_paper(e, summary_chars=SEARCH_SUMMARY_CHARS, detailed=False)
                for e in entries
            ],
        }

    @tools.tool(title="Get arXiv paper")
    async def arxiv_get_paper(
        arxiv_id: Annotated[
            str,
            Field(
                description="arXiv identifier such as '1706.03762', '2301.12345v2' or "
                "'hep-th/9901001'. An 'arXiv:' prefix or an arxiv.org/abs URL is also accepted."
            ),
        ],
    ) -> dict[str, Any]:
        """Fetch one arXiv paper by id: full abstract, authors, categories, dates, DOI,
        journal reference and PDF link."""
        paper_id = normalise_arxiv_id(arxiv_id)
        xml_text = await http.get_text(API_URL, {"id_list": paper_id, "max_results": 1})
        _, entries = parse_feed(xml_text)
        if not entries:
            raise InvalidInput(f"No arXiv paper found with id {paper_id!r}.")
        return entry_to_paper(entries[0], summary_chars=PAPER_SUMMARY_CHARS, detailed=True)
