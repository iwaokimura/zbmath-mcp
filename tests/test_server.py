"""Tests for zbmath-mcp server tools."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

MOCK_SEARCH_RESPONSE = {
    "status": {"nr_total_results": 2},
    "result": [
        {
            "id": 7192477,
            "title": {"title": "On the Riemann hypothesis"},
            "contributors": {"authors": [{"name": "Doe, John"}]},
            "year": 2020,
            "source": {"series": [{"title": "Annals of Mathematics"}]},
            "keywords": {"msc": [{"code": "11M26"}]},
            "editorial_contributions": [{"text": "A great paper."}],
        },
        {
            "id": 1234567,
            "title": {"title": "Spectral theory"},
            "contributors": {"authors": [{"name": "Smith, Jane"}]},
            "year": 2019,
            "source": {"series": []},
            "keywords": {"msc": [{"code": "35P15"}]},
            "editorial_contributions": [],
        },
    ],
}

MOCK_DOCUMENT_RESPONSE = {
    "result": {
        "id": 7192477,
        "title": {"title": "On the Riemann hypothesis"},
        "contributors": {"authors": [{"name": "Doe, John"}]},
        "year": 2020,
    }
}

MOCK_AUTHOR_RESPONSE = {
    "result": {
        "id": "euler.leonhard",
        "name": "Euler, Leonhard",
        "publications": 866,
    }
}

MOCK_SOFTWARE_RESPONSE = {
    "result": {
        "id": 825,
        "name": "Macaulay2",
        "description": "A software system for algebraic geometry.",
    }
}


# ---------------------------------------------------------------------------
# Patch helper
# ---------------------------------------------------------------------------

def _make_mock_http_response(data: dict) -> MagicMock:
    mock = MagicMock()
    mock.raise_for_status = MagicMock()
    mock.json = MagicMock(return_value=data)
    return mock


# ---------------------------------------------------------------------------
# Tests for search_documents
# ---------------------------------------------------------------------------

class TestSearchDocuments:
    @pytest.mark.asyncio
    async def test_returns_documents(self):
        from server import search_documents

        mock_response = _make_mock_http_response(MOCK_SEARCH_RESPONSE)
        with patch("server.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await search_documents("Riemann hypothesis")

        data = json.loads(result)
        assert data["total_results"] == 2
        assert len(data["documents"]) == 2
        assert data["documents"][0]["zbmath_id"] == 7192477
        assert data["documents"][0]["title"] == "On the Riemann hypothesis"
        assert data["documents"][0]["authors"] == ["Doe, John"]
        assert data["documents"][0]["msc_codes"] == ["11M26"]
        assert data["documents"][0]["url"].startswith("https://zbmath.org/?q=an:")

    @pytest.mark.asyncio
    async def test_correct_api_params(self):
        from server import search_documents

        mock_response = _make_mock_http_response({"status": {"nr_total_results": 0}, "result": []})
        with patch("server.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            await search_documents("test query", results_per_page=5, page=2)

        call_kwargs = mock_client.get.call_args
        assert call_kwargs[0][0] == "https://api.zbmath.org/v1/document/_search"
        params = call_kwargs[1]["params"]
        assert params["search_string"] == "test query"
        assert params["results_per_page"] == 5
        assert params["page"] == 2

    @pytest.mark.asyncio
    async def test_clamps_results_per_page(self):
        from server import search_documents

        mock_response = _make_mock_http_response({"status": {"nr_total_results": 0}, "result": []})
        with patch("server.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            await search_documents("test", results_per_page=200)

        params = mock_client.get.call_args[1]["params"]
        assert params["results_per_page"] == 100

    @pytest.mark.asyncio
    async def test_empty_results(self):
        from server import search_documents

        mock_response = _make_mock_http_response({"status": {"nr_total_results": 0}, "result": []})
        with patch("server.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await search_documents("xyzabcnonexistent")

        data = json.loads(result)
        assert data["total_results"] == 0
        assert data["documents"] == []

    @pytest.mark.asyncio
    async def test_second_doc_missing_review(self):
        from server import search_documents

        mock_response = _make_mock_http_response(MOCK_SEARCH_RESPONSE)
        with patch("server.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await search_documents("spectral theory")

        data = json.loads(result)
        assert data["documents"][1]["review"] == ""


# ---------------------------------------------------------------------------
# Tests for get_document
# ---------------------------------------------------------------------------

class TestGetDocument:
    @pytest.mark.asyncio
    async def test_returns_document(self):
        from server import get_document

        mock_response = _make_mock_http_response(MOCK_DOCUMENT_RESPONSE)
        with patch("server.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await get_document(7192477)

        data = json.loads(result)
        assert data["id"] == 7192477
        assert data["year"] == 2020

    @pytest.mark.asyncio
    async def test_calls_correct_url(self):
        from server import get_document

        mock_response = _make_mock_http_response(MOCK_DOCUMENT_RESPONSE)
        with patch("server.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            await get_document(7192477)

        url = mock_client.get.call_args[0][0]
        assert url == "https://api.zbmath.org/v1/document/7192477"


# ---------------------------------------------------------------------------
# Tests for structured_search
# ---------------------------------------------------------------------------

class TestStructuredSearch:
    @pytest.mark.asyncio
    async def test_sends_author_param(self):
        from server import structured_search

        mock_response = _make_mock_http_response({"status": {"nr_total_results": 0}, "result": []})
        with patch("server.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            await structured_search(author="euler.leonhard")

        params = mock_client.get.call_args[1]["params"]
        assert params["au"] == "euler.leonhard"

    @pytest.mark.asyncio
    async def test_sends_msc_param(self):
        from server import structured_search

        mock_response = _make_mock_http_response({"status": {"nr_total_results": 0}, "result": []})
        with patch("server.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            await structured_search(msc_code="11M26")

        params = mock_client.get.call_args[1]["params"]
        assert params["cc"] == "11M26"

    @pytest.mark.asyncio
    async def test_year_range_params(self):
        from server import structured_search

        mock_response = _make_mock_http_response({"status": {"nr_total_results": 0}, "result": []})
        with patch("server.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            await structured_search(year_from=2000, year_to=2010)

        params = mock_client.get.call_args[1]["params"]
        assert params["py_from"] == 2000
        assert params["py_to"] == 2010

    @pytest.mark.asyncio
    async def test_omits_empty_params(self):
        from server import structured_search

        mock_response = _make_mock_http_response({"status": {"nr_total_results": 0}, "result": []})
        with patch("server.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            await structured_search()

        params = mock_client.get.call_args[1]["params"]
        assert "au" not in params
        assert "ti" not in params
        assert "cc" not in params
        assert "py_from" not in params
        assert "py_to" not in params
        assert "so" not in params


# ---------------------------------------------------------------------------
# Tests for get_author
# ---------------------------------------------------------------------------

class TestGetAuthor:
    @pytest.mark.asyncio
    async def test_returns_author(self):
        from server import get_author

        mock_response = _make_mock_http_response(MOCK_AUTHOR_RESPONSE)
        with patch("server.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await get_author("euler.leonhard")

        data = json.loads(result)
        assert data["id"] == "euler.leonhard"
        assert data["name"] == "Euler, Leonhard"

    @pytest.mark.asyncio
    async def test_calls_correct_url(self):
        from server import get_author

        mock_response = _make_mock_http_response(MOCK_AUTHOR_RESPONSE)
        with patch("server.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            await get_author("euler.leonhard")

        url = mock_client.get.call_args[0][0]
        assert url == "https://api.zbmath.org/v1/author/euler.leonhard"


# ---------------------------------------------------------------------------
# Tests for get_software
# ---------------------------------------------------------------------------

class TestGetSoftware:
    @pytest.mark.asyncio
    async def test_returns_software(self):
        from server import get_software

        mock_response = _make_mock_http_response(MOCK_SOFTWARE_RESPONSE)
        with patch("server.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await get_software(825)

        data = json.loads(result)
        assert data["id"] == 825
        assert data["name"] == "Macaulay2"

    @pytest.mark.asyncio
    async def test_calls_correct_url(self):
        from server import get_software

        mock_response = _make_mock_http_response(MOCK_SOFTWARE_RESPONSE)
        with patch("server.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            await get_software(825)

        url = mock_client.get.call_args[0][0]
        assert url == "https://api.zbmath.org/v1/software/825"
