"""Wikipedia tools: full-text article search and page summaries from the MediaWiki REST APIs."""

import re
from typing import Annotated, Any
from urllib.parse import quote

from pydantic import Field

from keyless_mcp.core import (
    AdapterHttp,
    InvalidInput,
    ToolRegistry,
    UpstreamError,
    strip_html,
    truncate,
)

MAX_LIMIT = 20
SUMMARY_CHARS = 2000
EXCERPT_CHARS = 300

# Language editions are subdomains of wikipedia.org: "en", "de", "simple", "zh-yue". Validating
# the code also guarantees requests can only go to *.wikipedia.org.
LANG_RE = re.compile(r"^[a-z]{2,12}(-[a-z]{2,12})*$")


def check_lang(lang: str) -> str:
    code = lang.strip().lower()
    if not LANG_RE.match(code):
        raise InvalidInput(
            f"lang {lang!r} is not a Wikipedia language code. Use codes such as 'en', 'de', "
            "'fr', 'es', 'ja' or 'simple'."
        )
    return code


def article_url(lang: str, key: str) -> str:
    return f"https://{lang}.wikipedia.org/wiki/{quote(key, safe='()_,:')}"


def register(tools: ToolRegistry, http: AdapterHttp) -> None:
    @tools.tool(title="Search Wikipedia")
    async def wikipedia_search(
        query: Annotated[
            str,
            Field(
                description="Search terms, e.g. 'alan turing' or 'photosynthesis'. Matches "
                "article titles and text. Must not be empty."
            ),
        ],
        limit: Annotated[
            int, Field(description=f"How many articles to return, 1 to {MAX_LIMIT}. Default 5.")
        ] = 5,
        lang: Annotated[
            str,
            Field(
                description="Wikipedia language edition code, e.g. 'en' (default), 'de', 'fr', "
                "'es', 'ja', 'simple'."
            ),
        ] = "en",
    ) -> dict[str, Any]:
        """Search Wikipedia for articles matching some words. Returns the best matches with
        title, one-line description, a plain-text excerpt around the match and the article
        URL. Use wikipedia_get_summary with a returned title to read the article's intro."""
        if not query.strip():
            raise InvalidInput("query must not be empty.")
        if not 1 <= limit <= MAX_LIMIT:
            raise InvalidInput(f"limit must be between 1 and {MAX_LIMIT}.")
        code = check_lang(lang)
        data = await http.get_json(
            f"https://{code}.wikipedia.org/w/rest.php/v1/search/page",
            {"q": query.strip(), "limit": limit},
        )
        pages = data["pages"]
        return {
            "query": query.strip(),
            "lang": code,
            "returned": len(pages),
            "results": [
                {
                    "title": page["title"],
                    "description": page.get("description"),
                    "excerpt": truncate(strip_html(page.get("excerpt")), EXCERPT_CHARS),
                    "url": article_url(code, page["key"]),
                }
                for page in pages
            ],
        }

    @tools.tool(title="Get Wikipedia article summary")
    async def wikipedia_get_summary(
        title: Annotated[
            str,
            Field(
                description="Article title, e.g. 'Alan Turing' or 'Python (programming language)'. "
                "Redirects are followed. Use wikipedia_search first if unsure of the exact title."
            ),
        ],
        lang: Annotated[
            str,
            Field(
                description="Wikipedia language edition code, e.g. 'en' (default), 'de', 'fr', "
                "'es', 'ja', 'simple'."
            ),
        ] = "en",
    ) -> dict[str, Any]:
        """Get the introductory summary of one Wikipedia article: title, short description,
        the opening paragraph(s) as plain text, last-edit time and the article URL. Also flags
        disambiguation pages, which list several meanings instead of describing one topic."""
        name = title.strip()
        if not name:
            raise InvalidInput("title must not be empty.")
        code = check_lang(lang)
        slug = quote(name.replace(" ", "_"), safe="")
        try:
            data = await http.get_json(
                f"https://{code}.wikipedia.org/api/rest_v1/page/summary/{slug}"
            )
        except UpstreamError as exc:
            if exc.status == 404:
                raise InvalidInput(
                    f"No {code}.wikipedia.org article titled {name!r}. "
                    "Use wikipedia_search to find the exact title."
                ) from None
            raise
        page_url = data.get("content_urls", {}).get("desktop", {}).get("page")
        return {
            "title": data["title"],
            "description": data.get("description"),
            "summary": truncate(data["extract"], SUMMARY_CHARS),
            "is_disambiguation": data.get("type") == "disambiguation",
            "lang": code,
            "last_modified": data.get("timestamp"),
            "thumbnail": data.get("thumbnail", {}).get("source"),
            "url": page_url or article_url(code, data["title"].replace(" ", "_")),
        }
