import datetime
import math
import requests
from bs4 import BeautifulSoup
import json

class Tool:
    def __init__(self, name: str, description: str, func: callable):
        self.name = name
        self.description = description
        self.func = func

    def run(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def to_string(self):
        return f"{self.name}: {self.description}"


def get_current_time(*args, **kwargs):
    """Returns the current local time."""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def calculate(expression: str):
    """Evaluates a mathematical expression."""
    try:
        # Safety: Limit available names to math module
        allowed_names = {k: v for k, v in math.__dict__.items() if not k.startswith("__")}
        return str(eval(expression, {"__builtins__": {}}, allowed_names))
    except Exception as e:
        return f"Error: {e}"

def search_web(query: str, limit: int = 5):
    """
    Search the web using Google.
    Args:
        query: The search query string.
        limit: Max results (default 5, max 10).
    """
    try:
        limit = min(int(limit), 10)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get("https://www.google.com/search", params={"q": query}, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        results = []
        
        for g in soup.find_all('div', class_='g'):
            if len(results) >= limit:
                break
                
            title_element = g.find('h3')
            link_element = g.find('a')
            snippet_element = g.find('div', class_='VwiC3b') # Common class for snippets, might change
            
            if title_element and link_element:
                url = link_element.get('href')
                if url and url.startswith('http'):
                    results.append({
                        "title": title_element.get_text(),
                        "url": url,
                        "description": snippet_element.get_text() if snippet_element else ""
                    })
                    
        return json.dumps(results, indent=2)
    except Exception as e:
        return f"Search error: {e}"

# Registry of available tools
TOOLS = [
    Tool("get_current_time", "Returns the current local time. No arguments needed.", get_current_time),
    Tool("calculate", "Evaluates a mathematical expression (e.g., '2 + 2', 'sqrt(16)'). Input is a string expression.", calculate),
    Tool("search_web", "Search the web using Google. Input is a search query string.", search_web),
]
