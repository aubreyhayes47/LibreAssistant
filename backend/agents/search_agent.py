"""Search agent capable of using multiple providers."""

import logging
import os
from typing import Any, Dict, List

import aiohttp
from duckduckgo_search import AsyncDDGS

logger = logging.getLogger(__name__)


class SearchAgent:
    """Flexible search agent supporting multiple providers."""

    def __init__(
        self, provider: str = "duckduckgo", searx_url: str | None = None
    ) -> None:
        self.provider = provider.lower()
        self.searx_url = searx_url or os.getenv("SEARX_URL", "https://searx.org")
        self.ddg_backend = "lite"

    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Perform a web search and return results."""
        if self.provider == "duckduckgo":
            return await self._search_duckduckgo(query, max_results)
        if self.provider == "wikipedia":
            return await self._search_wikipedia(query, max_results)
        if self.provider == "searx":
            return await self._search_searx(query, max_results)

        raise ValueError(f"Unknown search provider: {self.provider}")

    async def _search_duckduckgo(
        self, query: str, max_results: int
    ) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        try:
            async with AsyncDDGS() as ddgs:
                async for r in ddgs.text(
                    query, backend=self.ddg_backend, max_results=max_results
                ):
                    results.append(
                        {
                            "title": r.get("title"),
                            "url": r.get("href"),
                            "body": r.get("body"),
                        }
                    )
                    if len(results) >= max_results:
                        break
        except Exception as e:  # pragma: no cover - network errors
            logger.error(f"DuckDuckGo search error: {e}")
        return results

    async def _search_wikipedia(
        self, query: str, max_results: int
    ) -> List[Dict[str, Any]]:
        """Use the Wikipedia API to search articles."""
        url = (
            "https://en.wikipedia.org/w/api.php?format=json&action=query&list=search"
            f"&srsearch={query}&srlimit={max_results}"
        )
        results: List[Dict[str, Any]] = []
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for item in data.get("query", {}).get("search", []):
                            results.append(
                                {
                                    "title": item.get("title"),
                                    "url": (
                                        "https://en.wikipedia.org/wiki/"
                                        f"{item.get('title').replace(' ', '_')}"
                                    ),
                                    "body": item.get("snippet"),
                                }
                            )
                            if len(results) >= max_results:
                                break
                    else:
                        logger.error(f"Wikipedia search HTTP {resp.status}")
        except Exception as e:  # pragma: no cover - network errors
            logger.error(f"Wikipedia search error: {e}")
        return results

    async def _search_searx(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search using a Searx instance."""
        api_url = (
            f"{self.searx_url}/search?q={query}&format=json&language=en"
            f"&safesearch=1&categories=general"
        )
        results: List[Dict[str, Any]] = []
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for item in data.get("results", [])[:max_results]:
                            results.append(
                                {
                                    "title": item.get("title"),
                                    "url": item.get("url"),
                                    "body": item.get("content"),
                                }
                            )
                    else:
                        logger.error(f"Searx search HTTP {resp.status}")
        except Exception as e:  # pragma: no cover - network errors
            logger.error(f"Searx search error: {e}")
        return results
