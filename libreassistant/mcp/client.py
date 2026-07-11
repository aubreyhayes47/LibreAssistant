"""JSON-RPC 2.0 MCP client supporting HTTP and stdio transports, with OAuth / PKCE flow integration."""
import json, re, select, subprocess, threading, time
from urllib.request import Request, urlopen
from urllib.error import URLError

from .oauth import authenticate_server, load_tokens, save_tokens, refresh_server_token

_RATE_LIMIT_DELAY_RE = re.compile(r"(?:expected available in|available in)\s+(\d+)\s+seconds?", re.IGNORECASE)


def _rate_limit_retry_delay(text: str) -> int | None:
    lower = text.lower()
    if "rate limit" not in lower and "throttled" not in lower and "http 429" not in lower:
        return None
    match = _RATE_LIMIT_DELAY_RE.search(text)
    if not match:
        return None
    return int(match.group(1)) + 1


class MCPClient:
    """A single MCP server client. Handles JSON-RPC lifecycle (initialize, tools/list, tools/call), transport dispatch, auth token management, and session tracking."""
    def __init__(self, name: str, config: dict):
        """... docstring ..."""
        self.name = name
        self.transport = config.get("transport", "http")
        self.url = config.get("url")
        self.command = config.get("command")
        self.args = config.get("args", [])
        self.oauth_config = config.get("oauth")  # None if transport is stdio or no OAuth is configured
        self._req_id = 0
        self._req_id_lock = threading.Lock()
        self._access_token = None
        self._session_id = None
        self._proc = None
        self._stdout_lock = threading.Lock()
        self._tools = []
        self._interactive_retry = True  # Set False during lazy_connect to avoid blocking on user interaction
        self._needs_auth = False
        self._config = config

    def _ensure_auth(self, interactive: bool = True, force: bool = False) -> bool:
        """Three-tier auth: cached token, refresh token, or interactive OAuth flow. Returns True if a valid access_token is available.
        Why three tiers?  Cached tokens are fastest (no network).  Refresh tokens avoid
        re-prompting the user when the token is merely expired.  Interactive OAuth is the
        last resort that opens a browser.  The 60-second buffer prevents using a token that
        would expire mid-request.
        """
        if force:  # force=True: discard any existing token before proceeding
            self._access_token = None
        if self._access_token:
            if not interactive:
                return True
            entry = load_tokens().get(self.name, {})
            expires_at = entry.get("expires_at", 0)
            if not expires_at or not isinstance(expires_at, (int, float)) or expires_at > time.time() + 60:  # Buffer of 60s prevents using a token that expires before the request completes
                return True
            # Attempt token refresh using stored refresh_token
            refresh = entry.get("refresh_token")
            if refresh:
                new_token = refresh_server_token(self.name, entry)
                if new_token:
                    self._access_token = new_token
                    return True
            self._access_token = None
        if not self.oauth_config or self.transport != "http":  # Non-OAuth server (stdio or no oauth config) — cannot authenticate interactively
            return False
        # Non-interactive mode: check cache without triggering browser flow
        if not interactive:
            entry = load_tokens().get(self.name, {})
            exp = entry.get("expires_at", 0)
            if entry.get("access_token") and isinstance(exp, (int, float)) and exp > time.time() + 60:
                self._access_token = entry["access_token"]
                return True
            return False
        token = authenticate_server(self.name, self.url, self.oauth_config, force=force)
        if token:
            self._access_token = token
            return True
        return False

    def _auth_header(self) -> dict:
        """Return Bearer token header if an access token is available."""
        if self._access_token:
            return {"Authorization": f"Bearer {self._access_token}"}
        return {}

    def _session_header(self) -> dict:
        """Return MCP session header if a session has been established."""
        if self._session_id:
            return {"mcp-session-id": self._session_id}
        return {}

    def _next_id(self) -> int:
        """Thread-safe incrementing JSON-RPC request ID."""
        with self._req_id_lock:
            self._req_id += 1
            return self._req_id

    @staticmethod
    def _parse_response(body: str) -> dict:
        """Parse JSON-RPC response, handling both plain JSON and Server-Sent Events (SSE) format.

        Why handle both?  The MCP spec allows HTTP servers to return JSON-RPC responses
        wrapped in SSE (Server-Sent Events) for streaming.  Some servers (e.g. CourtListener)
        use SSE framing even for single-response payloads; others return raw JSON.
        Detecting the SSE wrapper by checking for "event:" at the start lets us handle
        both transparently without the caller needing to know which format the server uses.
        """
        body = body.strip()
        if not body:
            return {}
        if body.startswith("event:"):  # SSE format: "event: ...\ndata: ..." — merge consecutive data lines
            parts = []
            for line in body.splitlines():
                if line.startswith("data:"):
                    parts.append(line[5:].strip())
            if parts:
                return json.loads("\n".join(parts))
            return {}
        return json.loads(body)

    def _send_http(self, body: dict) -> dict:
        """POST to HTTP MCP endpoint with retry (504) and interactive re-auth (401)."""
        max_attempts = 3  # Retry up to 3 times with exponential backoff on 504 Gateway Timeout
        for attempt in range(max_attempts):
            data = json.dumps(body).encode()
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            }
            headers.update(self._auth_header())
            headers.update(self._session_header())
            req = Request(self.url, data=data, headers=headers)
            try:
                resp = urlopen(req, timeout=120)
                sid = resp.headers.get("mcp-session-id")  # Persist session ID from response header for subsequent requests
                if sid:
                    self._session_id = sid
                try:
                    return self._parse_response(resp.read().decode())
                except Exception:
                    self._session_id = None
                    raise
            except URLError as e:
                # 504: transient — retry with backoff; 401: token expired — attempt interactive re-auth once
                if hasattr(e, "code"):
                    if e.code == 504 and attempt < max_attempts - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s, (then give up).
                        # Why exponential (not fixed delay)?  504 means the upstream MCP server
                        # is still initializing or temporarily overloaded.  Exponential backoff
                        # gives the server progressively more time to recover, while a fixed delay
                        # either wastes time (if too long) or retries too aggressively (if too short).
                        # 3 attempts with 1s + 2s = 3s total wait before giving up.
                        continue
                    if e.code == 401 and self.oauth_config and self._interactive_retry:  # Interactive retry: re-auth with force=True and retry the request once
                        self._access_token = None
                        self._session_id = None
                        if attempt == 0 and self._ensure_auth(interactive=True, force=True):
                            continue
                        self._needs_auth = True
                self._session_id = None
                if hasattr(e, "read"):
                    try:
                        return self._parse_response(e.read().decode())
                    except Exception:
                        pass
                raise

    def _send_stdio(self, body: dict) -> dict:
        """Write JSON-RPC to subprocess stdin, read response from stdout with 30s timeout.

        Why the _stdout_lock?  The stdio MCP protocol is request-response: we write one
        JSON-RPC message and expect exactly one JSON-RPC response on stdout.  If two
        threads sent requests concurrently, their responses would interleave on stdout,
        making it impossible to match responses to requests.  The lock serializes
        write-read pairs so each thread gets its own complete response.
        """
        if not self._proc or self._proc.poll() is not None:
            raise RuntimeError(f"MCP client {self.name}: subprocess not running")
        line = json.dumps(body) + "\n"
        with self._stdout_lock:
            self._proc.stdin.write(line)
            self._proc.stdin.flush()
            try:
                ready, _, _ = select.select([self._proc.stdout], [], [], 30)  # select.select with timeout guards against hung subprocess; fallback pass on Windows ValueError
                if not ready:
                    raise RuntimeError(f"MCP client {self.name}: subprocess timed out (30s)")
            except (TypeError, ValueError):
                pass
            resp_line = self._proc.stdout.readline()
        if not resp_line:
            raise RuntimeError(f"MCP client {self.name}: subprocess closed stdout")
        return self._parse_response(resp_line)

    def _send(self, body: dict) -> dict:
        """Transport dispatcher: route to stdio or HTTP based on self.transport.
        Why support both?  HTTP is the standard for remote MCP servers (OAuth-protected
        APIs like CourtListener).  stdio is used for local tool servers (e.g. a Python
        script launched as a subprocess) — no network overhead, no auth needed, just
        pipe-based JSON-RPC.  The dispatch lets both coexist under one client interface.
        """
        if self.transport == "stdio":
            return self._send_stdio(body)
        return self._send_http(body)

    def _send_request(self, method: str, params: dict | None = None) -> dict:
        """Build a JSON-RPC 2.0 request with auto-incrementing ID."""
        body = {"jsonrpc": "2.0", "id": self._next_id(), "method": method}
        if params is not None:
            body["params"] = params
        return self._send(body)

    def _send_notification(self, method: str, params: dict | None = None) -> None:
        """Send a JSON-RPC 2.0 notification (no ID, no response expected)."""
        body = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            body["params"] = params
        self._send(body)

    def _start_subprocess(self):
        """Launch the stdio subprocess and start a daemon thread to drain stderr."""
        self._proc = subprocess.Popen(
            [self.command] + self.args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self._stderr_thread = threading.Thread(
            target=self._read_stderr, daemon=True
        )
        self._stderr_thread.start()  # Daemon thread silently drains stderr to prevent kernel pipe buffer deadlock

    def lazy_connect(self) -> list[dict]:
        """Attempt non-interactive connection using cached auth only. Returns tool list on success, empty list if auth is needed, raises on real errors.

        Why lazy_connect() vs finish_connect()?  At startup, we don't want to block
        or open browsers for servers the user hasn't authenticated yet.  lazy_connect()
        tries only cached/refreshed tokens (interactive=False); if that fails, it sets
        _needs_auth and returns an empty list so MCPManager can register a stub tool
        instead.  finish_connect() is called later — only when the user explicitly asks
        to authenticate — and runs the full browser-based OAuth flow.
        """
        if self.transport == "stdio":
            self._start_subprocess()

        self._ensure_auth(interactive=False)
        self._session_id = None
        self._interactive_retry = False

        try:
            init_result = self._send_request("initialize", {
                "protocolVersion": "2025-11-25",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "LibreAssistant", "version": "0.1.0"},
            })
        except Exception as e:
            self._needs_auth = bool(self.oauth_config and self.transport == "http")
            if self._needs_auth:
                return []
            raise

        if "error" in init_result:
            err = init_result["error"]
            msg = err.get("message", str(err)) if isinstance(err, dict) else str(err)
            self._needs_auth = bool(self.oauth_config and self.transport == "http")
            if self._needs_auth:
                return []
            raise RuntimeError(f"MCP initialize error: {msg}")

        self._send_notification("notifications/initialized")

        tools_result = self._send_request("tools/list")
        if "error" in tools_result:
            err = tools_result["error"]
            msg = err.get("message", str(err)) if isinstance(err, dict) else str(err)
            raise RuntimeError(f"MCP tools/list error: {msg}")
        self._tools = tools_result.get("result", {}).get("tools", [])
        self._interactive_retry = True
        return self._tools

    def finish_connect(self, force: bool = False) -> list[dict]:
        """Interactive connection: runs full OAuth flow (if needed), re-initializes session, and returns tool list."""
        if not self._ensure_auth(interactive=True, force=force):
            raise RuntimeError(f"Authentication failed for {self.name}")
        self._session_id = None
        self._interactive_retry = True
        init_result = self._send_request("initialize", {
            "protocolVersion": "2025-11-25",
            "capabilities": {"tools": {}},
            "clientInfo": {"name": "LibreAssistant", "version": "0.1.0"},
        })
        if "error" in init_result:
            err = init_result["error"]
            msg = err.get("message", str(err)) if isinstance(err, dict) else str(err)
            raise RuntimeError(f"MCP initialize error: {msg}")
        self._send_notification("notifications/initialized")
        tools_result = self._send_request("tools/list")
        if "error" in tools_result:
            err = tools_result["error"]
            msg = err.get("message", str(err)) if isinstance(err, dict) else str(err)
            raise RuntimeError(f"MCP tools/list error: {msg}")
        self._tools = tools_result.get("result", {}).get("tools", [])
        self._needs_auth = False
        return self._tools

    def _read_stderr(self):
        """Daemon target: consume stderr line-by-line until the subprocess exits, preventing pipe deadlocks."""
        if self._proc and self._proc.stderr:
            for _ in self._proc.stderr:
                pass

    def _format_tool_result(self, name: str, result: dict) -> str:
        """Convert an MCP tools/call JSON-RPC response into user-visible text."""
        if "error" in result:
            msg = result['error'].get('message', 'unknown')
            if "unauthorized" in msg.lower() and "opinion" in name.lower():
                msg += (" (Hint: did you pass a cluster_id as opinion_id? "
                        "They are different — use the opinion_id field from the "
                        "opinion records, not cluster_id from search results.)")
            return f"Error: {msg}"
        content_list = result.get("result", {}).get("content", [])
        texts = []
        for item in content_list:
            if item.get("type") == "text":
                texts.append(item.get("text", ""))
            elif item.get("type") == "resource":
                texts.append(str(item.get("resource", {})))
        return "\n".join(texts) if texts else "(no content returned)"

    def call_tool(self, name: str, arguments: dict) -> str:
        """Execute a tool on the server and format the result as a plain string for LLM consumption.

        The IncompleteRead retry (attempt 0 → sleep 1s → retry) handles a common
        race with HTTP servers that close the connection before the full response body
        is flushed.  A single retry with a brief pause is sufficient because this is
        a transient transport error, not a server-side failure.
        """
        for attempt in range(2):
            try:
                result = self._send_request("tools/call", {"name": name, "arguments": arguments})
            except Exception as e:
                if attempt == 0 and "IncompleteRead" in type(e).__name__:
                    time.sleep(1)
                    continue
                raise
            text = self._format_tool_result(name, result)
            delay = _rate_limit_retry_delay(text)
            if delay is not None and attempt == 0:
                time.sleep(min(delay, 65))
                continue
            return text
        return "(no content returned)"

    @property
    def tools(self) -> list[dict]:
        """The list of tools fetched from the server after initialization."""
        return self._tools

    def disconnect(self):
        """Terminate the subprocess with SIGTERM, fall back to SIGKILL after 5s timeout.

        Why the escalation?  SIGTERM lets the subprocess clean up (flush buffers,
        close sockets, release temp files).  If it doesn't exit within 5 seconds
        (e.g. it's stuck or ignoring SIGTERM), SIGKILL forces immediate termination.
        The second wait(5) after SIGKILL ensures the process is fully reaped before
        we clear self._proc, preventing zombie processes.
        """
        if self._proc:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._proc.kill()
                self._proc.wait(timeout=5)
            self._proc = None
