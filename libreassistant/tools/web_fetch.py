"""Fetch and extract text from URLs with size limits, HTML stripping, and security checks."""
import random
from html.parser import HTMLParser

import requests

MAX_SIZE = 2 * 1024 * 1024  # 2 MB — hard limit on response body to prevent OOM
CHUNK_SIZE = 512 * 1024  # 512 KB chunks — balances memory usage vs. throughput during streaming

# Rotate User-Agent to reduce blocking from bot-detection heuristics
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]

SKIP_TAGS = {"script", "style", "noscript", "iframe", "object", "embed"}  # HTML tags whose content is stripped during text extraction (non-content containers)


class _HTMLStripper(HTMLParser):
    """Custom HTML parser that tracks skip-depth for nested <script>/<style> blocks when extracting plain text."""
    def __init__(self):
        super().__init__()
        self._skip_depth = 0
        self._parts = []

    # Increment depth counter so nested skipped tags remain hidden
    def handle_starttag(self, tag, attrs):
        if self._skip_depth > 0 or tag in SKIP_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag):
        if self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data):
        if self._skip_depth == 0:
            self._parts.append(data)

    def text(self) -> str:
        """Collapse collected text by stripping whitespace per line and dropping empty lines."""
        raw = "".join(self._parts)
        lines = [l.strip() for l in raw.splitlines()]
        return "\n".join(l for l in lines if l)


def _strip_html(html: str) -> str:
    """Convenience wrapper that feeds HTML into _HTMLStripper and returns cleaned text."""
    stripper = _HTMLStripper()
    stripper.feed(html)
    return stripper.text()


def _sniff_is_pdf(data: bytes) -> bool:
    """Check magic bytes — catches PDFs served with wrong or missing Content-Type headers (defence in depth)."""
    return data[:5] == b"%PDF-"


def fetch_url(args: dict) -> str:
    """Fetch a URL and return its content as text or raw HTML. Applies: streaming with size limit, redirect-security checks, Cloudflare bypass, encoding detection, and HTML stripping."""
    url = args.get("url", "")
    fmt = args.get("format", "text")

    if not url.startswith(("http://", "https://")):  # Only http/https permitted — file://, ftp://, etc. are blocked for security
        return "Error: only http/https URLs allowed"

    if fmt not in ("text", "html"):
        return f"Error: unknown format '{fmt}'; use 'text' or 'html'"

    ua = random.choice(USER_AGENTS)  # Random UA choice per request to evade fingerprinting

    try:
        resp = requests.get(url, stream=True, timeout=(10, 30), headers={  # stream=True enables chunked reading for the size cap below
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        })
    except requests.exceptions.Timeout:
        return f"Error fetching {url}: request timed out (connect: 10s, read: 30s)"
    except requests.exceptions.RequestException as e:
        return f"Error fetching {url}: {e}"

    # Reject HTTPS→HTTP redirect chain (SSL stripping attack)
    if resp.history:
        for r in resp.history:
            if r.url.startswith("https://") and resp.url.startswith("http://"):
                return (
                    f"Error fetching {url}: HTTPS→HTTP redirect downgrade detected "
                    f"({r.url} → {resp.url}). Blocked for security."
                )

    # Retry with an honest UA when Cloudflare sends a 403 — the spoofed browser UA may trigger challenges
    if resp.status_code == 403 and "cf-mitigated" in resp.headers.get("Server", "").lower():
        try:
            resp = requests.get(url, stream=True, timeout=(10, 30), headers={
                "User-Agent": "LibreAssistant/1.0",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            })
        except requests.exceptions.RequestException as e:
            return f"Error fetching {url} (Cloudflare bypass failed): {e}"

        # Validate redirect chain — reject HTTPS→HTTP downgrade
        if resp.history:
            for r in resp.history:
                if r.url.startswith("https://") and resp.url.startswith("http://"):
                    return (
                        f"Error fetching {url}: HTTPS→HTTP redirect downgrade detected "
                        f"({r.url} → {resp.url}). Blocked for security."
                    )

    # Final 403 after Cloudflare retry — surface actionable advice
    if resp.status_code == 403:
        return (
            f"Error fetching {url}: HTTP 403 Forbidden. "
            "The site may be blocking automated requests. "
            "Try using the terminal tool with curl instead."
        )

    if resp.status_code != 200:
        return f"Error fetching {url}: HTTP {resp.status_code}"

    ctype = (resp.headers.get("content-type") or "").split(";")[0].strip().lower()  # Normalise Content-Type by stripping parameters like charset
    if ctype == "application/pdf":
        return (
            f"Content is a PDF ({resp.headers.get('content-length', 'unknown')} bytes). "
            "The web_fetch tool cannot extract text from PDFs. "
            "Use the terminal tool with a command like: curl -sL '<url>' -o /tmp/doc.pdf && pdftotext /tmp/doc.pdf -"
        )

    # Images cannot be rendered in a text-only interface
    if ctype.startswith("image/"):
        return f"Content is an image ({ctype}, {resp.headers.get('content-length', 'unknown')} bytes). Cannot display images."

    body_chunks = []
    total = 0
    for chunk in resp.iter_content(CHUNK_SIZE, decode_unicode=False):
        if chunk:
            body_chunks.append(chunk)
            total += len(chunk)
            if total >= MAX_SIZE:
                break

    raw_bytes = b"".join(body_chunks)

    # Second PDF check — catches mislabelled content served with a generic Content-Type
    # Sniff PDF by magic bytes even if content-type is wrong
    if _sniff_is_pdf(raw_bytes[:100]):
        return (
            f"Content is a PDF ({total} bytes detected by signature). "
            "The web_fetch tool cannot extract text from PDFs. "
            "Use the terminal tool with: curl -sL '<url>' -o /tmp/doc.pdf && pdftotext /tmp/doc.pdf -"
        )

    # Honour explicit charset from Content-Type header; fall back to UTF-8 with replacement
    # Decode
    content_type = resp.headers.get("content-type", "")
    encoding = "utf-8"
    if "charset=" in content_type:
        encoding = content_type.split("charset=")[-1].split(";")[0].strip()
    try:
        text = raw_bytes.decode(encoding)
    except (LookupError, UnicodeDecodeError):
        text = raw_bytes.decode("utf-8", errors="replace")

    was_truncated = total >= MAX_SIZE

    # Strip HTML tags only when the caller requests plain-text format
    if fmt == "text":
        text = _strip_html(text)
        if not text.strip():
            text = "(page appears blank after stripping HTML — try format='html')"

    # Append truncation or emptiness warning footers
    if was_truncated:
        text += "\n\n[truncated at 2 MB]"
    elif len(raw_bytes) < 200:
        text += "\n\n(very short response — may be an error page or redirect)"

    return text
