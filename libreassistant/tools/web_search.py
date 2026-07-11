"""Adapter that exposes the DuckDuckGo search client as a tool handler."""
from ..search import search_web

def handle_web_search(args: dict) -> str:
    """Run a web search and format results as a plain-text digest. Maximum 10 results regardless of caller request."""
    query = args.get("query", "")
    max_results = min(args.get("max_results", 5), 10)  # Hard cap at 10 results to limit context consumption
    results = search_web(query, max_results=max_results)
    if not results:
        return "No results found."
    lines = []
    for r in results:
        lines.append(f"{r['title']}\n{r['href']}\n{r['body']}\n")
    return "\n".join(lines)
