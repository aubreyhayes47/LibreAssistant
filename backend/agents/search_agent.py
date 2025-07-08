import logging
from typing import Any, Dict, List

from duckduckgo_search import AsyncDDGS

logger = logging.getLogger(__name__)


class SearchAgent:
    """Simple web search agent using DuckDuckGo."""

    def __init__(self) -> None:
        self.backend = "lite"

    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Perform a web search and return results."""
        results: List[Dict[str, Any]] = []
        try:
            async with AsyncDDGS() as ddgs:
                async for r in ddgs.text(
                    query, backend=self.backend, max_results=max_results
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
            logger.error(f"Search error: {e}")
        return results
