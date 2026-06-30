"""zbMath MCP server — exposes zbMath Open REST API as MCP tools."""

from __future__ import annotations

import json
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

ZBMATH_API_BASE = "https://api.zbmath.org/v1"

mcp = FastMCP(
    "zbmath",
    instructions=(
        "Tools for searching and retrieving mathematical literature from "
        "zbMath Open (https://zbmath.org), the world's most comprehensive "
        "database for mathematical publications."
    ),
)


async def _get(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Send a GET request to the zbMath API and return the parsed JSON."""
    url = f"{ZBMATH_API_BASE}{path}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def search_documents(
    query: str,
    results_per_page: int = 10,
    page: int = 0,
) -> str:
    """Search zbMath Open for mathematical documents using a free-text query.

    Args:
        query: Free-text search string, e.g. "Riemann hypothesis" or
               "spectral theory elliptic operators".
        results_per_page: Number of results to return (1–100, default 10).
        page: Zero-based page index for pagination (default 0).

    Returns:
        JSON string containing total result count and a list of matching
        documents, each with id, title, authors, year, journal, MSC codes,
        a short review excerpt, and a zbMath URL.
    """
    results_per_page = max(1, min(results_per_page, 100))
    data = await _get(
        "/document/_search",
        params={
            "search_string": query,
            "page": page,
            "results_per_page": results_per_page,
        },
    )

    total = data.get("status", {}).get("nr_total_results", 0)
    documents = []
    for doc in data.get("result", []):
        title_field = doc.get("title", {})
        title = (
            title_field.get("title", "")
            if isinstance(title_field, dict)
            else str(title_field)
        )
        authors = [
            a.get("name", "")
            for a in doc.get("contributors", {}).get("authors", [])
        ]
        source = doc.get("source", {})
        series = source.get("series", [])
        journal = ""
        if isinstance(series, list) and series:
            journal = series[0].get("title", "")
        elif isinstance(series, dict):
            journal = series.get("title", "")

        msc_codes = [
            m.get("code", "")
            for m in doc.get("keywords", {}).get("msc", [])
        ]
        reviews = doc.get("editorial_contributions", [])
        review_text = reviews[0].get("text", "") if reviews else ""

        documents.append(
            {
                "zbmath_id": doc.get("id"),
                "title": title,
                "authors": authors,
                "year": doc.get("year"),
                "journal": journal,
                "msc_codes": msc_codes,
                "review": review_text[:400] if review_text else "",
                "url": f"https://zbmath.org/?q=an:{doc.get('id')}",
            }
        )

    return json.dumps(
        {"total_results": total, "page": page, "documents": documents},
        ensure_ascii=False,
        indent=2,
    )


@mcp.tool()
async def get_document(zbmath_id: int) -> str:
    """Retrieve full metadata for a single zbMath document by its numeric ID.

    Args:
        zbmath_id: The numeric zbMath document identifier
                   (e.g. 7192477 for Zbl 7192477).

    Returns:
        JSON string with complete document metadata including title, authors,
        abstract, MSC classification, journal, DOI, review, and links.
    """
    data = await _get(f"/document/{zbmath_id}")
    result = data.get("result", {})
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
async def structured_search(
    author: str = "",
    title: str = "",
    msc_code: str = "",
    year_from: int | None = None,
    year_to: int | None = None,
    journal: str = "",
    results_per_page: int = 10,
    page: int = 0,
) -> str:
    """Search zbMath documents using structured field filters.

    Use this instead of search_documents when you want to restrict results
    to specific fields such as author name, MSC subject class, or year range.

    Args:
        author: Author name or zbMath author profile string (e.g. "euler.leonhard").
        title: Words or phrases to match in the document title.
        msc_code: MSC 2020 classification code prefix, e.g. "11" for
                  Number Theory or "35J15" for a specific code.
        year_from: Earliest publication year (inclusive).
        year_to:   Latest publication year (inclusive).
        journal: Journal or series name fragment.
        results_per_page: Number of results (1–100, default 10).
        page: Zero-based page index for pagination (default 0).

    Returns:
        JSON string with total result count and matching documents.
    """
    results_per_page = max(1, min(results_per_page, 100))
    params: dict[str, Any] = {
        "page": page,
        "results_per_page": results_per_page,
    }
    if author:
        params["au"] = author
    if title:
        params["ti"] = title
    if msc_code:
        params["cc"] = msc_code
    if year_from is not None:
        params["py_from"] = year_from
    if year_to is not None:
        params["py_to"] = year_to
    if journal:
        params["so"] = journal

    data = await _get("/document/_structured_search", params=params)

    total = data.get("status", {}).get("nr_total_results", 0)
    documents = []
    for doc in data.get("result", []):
        title_field = doc.get("title", {})
        doc_title = (
            title_field.get("title", "")
            if isinstance(title_field, dict)
            else str(title_field)
        )
        authors = [
            a.get("name", "")
            for a in doc.get("contributors", {}).get("authors", [])
        ]
        msc_codes = [
            m.get("code", "")
            for m in doc.get("keywords", {}).get("msc", [])
        ]
        documents.append(
            {
                "zbmath_id": doc.get("id"),
                "title": doc_title,
                "authors": authors,
                "year": doc.get("year"),
                "msc_codes": msc_codes,
                "url": f"https://zbmath.org/?q=an:{doc.get('id')}",
            }
        )

    return json.dumps(
        {"total_results": total, "page": page, "documents": documents},
        ensure_ascii=False,
        indent=2,
    )


@mcp.tool()
async def get_author(author_id: str) -> str:
    """Retrieve profile information for a zbMath author by their profile ID.

    Args:
        author_id: The zbMath author profile identifier string,
                   e.g. "euler.leonhard" or "gauss.carl-friedrich".

    Returns:
        JSON string with the author's profile data including name variants,
        affiliated institutions, and publication count.
    """
    data = await _get(f"/author/{author_id}")
    result = data.get("result", {})
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
async def get_software(software_id: int) -> str:
    """Retrieve metadata for a zbMath / swMath software entry by its numeric ID.

    Args:
        software_id: The numeric swMath software identifier.

    Returns:
        JSON string with software metadata including name, description,
        programming language, keywords, and references.
    """
    data = await _get(f"/software/{software_id}")
    result = data.get("result", {})
    return json.dumps(result, ensure_ascii=False, indent=2)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
