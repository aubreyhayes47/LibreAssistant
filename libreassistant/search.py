"""DuckDuckGo web-search client wrapper with warning suppression for library rename."""
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*renamed to ddgs.*")  # Suppress ``DDGS`` renamed from ``ddg`` — harmless, controlled by us
# Why a wrapper instead of calling DDGS directly from tool handlers?
# The adapter pattern centralizes error handling: callers always get a list[dict],
# never an exception.  This keeps the tool handler contract simple — the model
# doesn't need to handle error strings, just an empty or error-keyed list.
# Why DuckDuckGo?  No API key required, no rate-limiting headers, generous
# result-volume allowance.  Suitable for a dev-tool assistant where perfect
# search recall isn't critical.
from ddgs import DDGS  # ``DDGS`` = DuckDuckGo Search — community-maintained wrapper
# Note: the import is at module level (not deferred inside search_web()) because DDGS
# is listed in pyproject.toml as a hard dependency.  No lazy-loading needed.

def search_web(query: str, max_results: int = 5) -> list[dict]:
    """Search the web via DuckDuckGo. Returns a list of result dicts with title/body/href keys. Network errors surface as an empty list."""
    # Why list[dict] instead of a typed dataclass or Enum?  The search adapter is a
    # thin wire format boundary: results flow directly into tool handlers that expect
    # plain dicts.  Introducing a domain class would add an extra conversion step for
    # no structural benefit.
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        return [
            {"title": r.get("title", ""), "body": r.get("body", ""), "href": r.get("href", "")}
            for r in results
        ]
    except Exception as e:
        return [{"error": str(e)}]  # Return error as list item (not raising) — keeps the calling code simple: it can always iterate over results
