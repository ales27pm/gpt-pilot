from unittest.mock import AsyncMock, patch

import pytest

from core.web.search import BraveSearchError, brave_search


@pytest.mark.asyncio
async def test_brave_search_fetches_and_extracts(monkeypatch):
    sample_json = {"web": {"results": [{"url": "https://example.com", "title": "Example", "description": "desc"}]}}

    class MockResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self):
            return sample_json

    async def mock_get(self, url, params=None, headers=None):
        assert url.startswith("https://api.search.brave.com")
        return MockResponse()

    monkeypatch.setenv("BRAVE_API_KEY", "test-key")
    with (
        patch("httpx.AsyncClient.get", new=mock_get),
        patch("trafilatura.fetch_url", return_value="<html></html>"),
        patch("trafilatura.extract", return_value="content"),
    ):
        results = await brave_search("test query", count=1)

    assert len(results) == 1
    result = results[0]
    assert result.url == "https://example.com"
    assert result.title == "Example"
    assert result.snippet == "desc"
    assert result.content == "content"
    assert result.trusted is False
    assert result.verified is False


@pytest.mark.asyncio
async def test_brave_search_requires_api_key(monkeypatch):
    monkeypatch.delenv("BRAVE_API_KEY", raising=False)
    with pytest.raises(BraveSearchError):
        await brave_search("query")


@pytest.mark.asyncio
async def test_brave_search_without_fetch_content(monkeypatch):
    sample_json = {"web": {"results": [{"url": "https://example.com", "title": "Example"}]}}

    class MockResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self):
            return sample_json

    async def mock_get(self, url, params=None, headers=None):
        return MockResponse()

    fetch_mock = AsyncMock(return_value="should not happen")
    monkeypatch.setenv("BRAVE_API_KEY", "test-key")
    with patch("httpx.AsyncClient.get", new=mock_get), patch("core.web.search._fetch_content", fetch_mock):
        results = await brave_search("q", fetch_content=False)

    fetch_mock.assert_not_awaited()
    assert results[0].content == ""


@pytest.mark.asyncio
async def test_brave_search_marks_trusted_sources(monkeypatch):
    sample_json = {"web": {"results": [{"url": "https://www.wikipedia.org/wiki/AI", "title": "AI"}]}}

    class MockResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self):
            return sample_json

    async def mock_get(self, url, params=None, headers=None):
        return MockResponse()

    fetch_mock = AsyncMock(return_value="content")
    monkeypatch.setenv("BRAVE_API_KEY", "test-key")
    with patch("httpx.AsyncClient.get", new=mock_get), patch("core.web.search._fetch_content", fetch_mock):
        results = await brave_search("q", count=1)

    assert results[0].trusted is True


@pytest.mark.asyncio
async def test_brave_search_fact_checks_overlapping_content(monkeypatch):
    sample_json = {
        "web": {
            "results": [
                {"url": "https://a.com", "title": "A"},
                {"url": "https://b.com", "title": "B"},
            ]
        }
    }

    class MockResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self):
            return sample_json

    async def mock_get(self, url, params=None, headers=None):
        return MockResponse()

    content_mock = AsyncMock(side_effect=["same text", "same text"])
    monkeypatch.setenv("BRAVE_API_KEY", "test-key")
    with patch("httpx.AsyncClient.get", new=mock_get), patch("core.web.search._fetch_content", content_mock):
        results = await brave_search("q", count=2)

    assert all(r.verified for r in results)
