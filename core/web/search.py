"""Utilities for searching the web using Brave Search API.

This module exposes :func:`brave_search` which queries the Brave
search API and returns page contents extracted with ``trafilatura``.
"""

from __future__ import annotations

import asyncio
import difflib
import os
from dataclasses import dataclass
from typing import Iterable, List, Optional
from urllib.parse import urlparse

import httpx
import trafilatura

BRAVE_SEARCH_API = "https://api.search.brave.com/res/v1/web/search"

# A modest list of domains generally considered reliable. The list is not
# exhaustive but is sufficient for basic trust heuristics and can be
# overridden by passing ``trusted_domains`` to :func:`brave_search`.
DEFAULT_TRUSTED_DOMAINS = {
    "wikipedia.org",
    "bbc.com",
    "nytimes.com",
    "nature.com",
    "nasa.gov",
    "who.int",
}


@dataclass
class WebResult:
    """Represents a single search result."""

    url: str
    title: str
    content: str
    snippet: Optional[str] = None
    trusted: bool = False
    verified: bool = False


class BraveSearchError(Exception):
    """Raised when Brave search cannot be performed."""


async def brave_search(
    query: str,
    *,
    count: int = 5,
    api_key: Optional[str] = None,
    fetch_content: bool = True,
    max_concurrency: int = 5,
    trusted_domains: Optional[Iterable[str]] = None,
) -> List[WebResult]:
    """Search the web using Brave search API.

    This function queries Brave search and downloads the contents of each
    result using :mod:`trafilatura`.

    Parameters
    ----------
    query:
        Search query.
    count:
        Number of results to fetch. Defaults to 5.
    api_key:
        Optional API key. If not provided, ``BRAVE_API_KEY`` environment
        variable is used.
    fetch_content:
        Whether to download and extract the textual content for each result.
        If ``False`` the ``content`` field of each :class:`WebResult` will be an
        empty string. Defaults to ``True``.
    max_concurrency:
        Maximum number of concurrent content fetches when ``fetch_content`` is
        enabled. Defaults to ``5``.
    trusted_domains:
        Iterable of domain names to treat as trusted. If ``None`` the
        :data:`DEFAULT_TRUSTED_DOMAINS` list is used.
    """

    key = api_key or os.getenv("BRAVE_API_KEY")
    if not key:
        raise BraveSearchError("Brave Search API key is required")

    headers = {"Accept": "application/json", "X-Subscription-Token": key}
    params = {"q": query, "count": count}

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(BRAVE_SEARCH_API, params=params, headers=headers)
        resp.raise_for_status()

    data = resp.json()
    web_results = data.get("web", {}).get("results", [])
    results: List[WebResult] = []

    async def fetch_with_sem(url: str, sem: asyncio.Semaphore) -> str:
        async with sem:
            return await _fetch_content(url)

    sem = asyncio.Semaphore(max_concurrency)
    tasks = []
    items = []
    for item in web_results:
        url = item.get("url")
        if not url:
            continue
        title = item.get("title", "")
        snippet = item.get("description") or item.get("snippet")
        items.append((url, title, snippet))
        if fetch_content:
            tasks.append(asyncio.create_task(fetch_with_sem(url, sem)))
        else:
            tasks.append(asyncio.create_task(asyncio.sleep(0, result="")))

    contents = await asyncio.gather(*tasks, return_exceptions=True)

    for (url, title, snippet), content in zip(items, contents):
        if isinstance(content, Exception):
            content = ""
        results.append(WebResult(url=url, title=title, snippet=snippet, content=content))

    _evaluate_results(results, trusted_domains or DEFAULT_TRUSTED_DOMAINS)
    return results


async def _fetch_content(url: str) -> str:
    """Fetch and extract textual content from a URL."""

    def fetch() -> str:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return ""
        extracted = trafilatura.extract(downloaded)
        return extracted or ""

    return await asyncio.to_thread(fetch)


def _evaluate_results(results: List[WebResult], trusted_domains: Iterable[str]) -> None:
    """Annotate results with trust and verification metadata.

    Parameters
    ----------
    results:
        Search results to annotate in-place.
    trusted_domains:
        Domains considered trustworthy. Subdomains of the entries are also
        treated as trusted.
    """

    domain_set = {d.lower() for d in trusted_domains}
    for res in results:
        domain = urlparse(res.url).netloc.lower()
        if any(domain == d or domain.endswith("." + d) for d in domain_set):
            res.trusted = True

    # Mark results as verified when similar content appears in multiple sources
    for i, a in enumerate(results):
        for b in results[i + 1 :]:
            if _similar_text(a.content, b.content):
                a.verified = True
                b.verified = True


def _similar_text(a: str, b: str, threshold: float = 0.3) -> bool:
    """Return ``True`` if two texts are similar based on a ratio threshold."""

    if not a or not b:
        return False
    return difflib.SequenceMatcher(None, a, b).ratio() >= threshold
