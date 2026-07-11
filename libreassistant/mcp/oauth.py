"""OAuth 2.0 PKCE authorization flow for MCP servers, including Dynamic Client Registration (DCR), local redirect server, and token persistence."""
import base64, hashlib, json, os, secrets, subprocess, threading, time, urllib.parse, webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError

from ..config import CONFIG_DIR

TOKEN_PATH = CONFIG_DIR / "mcp_tokens.json"  # Path to the JSON file storing access tokens, refresh tokens, and client metadata

_log_callback = print  # Default logger; replaced by set_log_callback() for integration with the app's UI

def set_log_callback(fn):
    """Override the global logger function (e.g. to route auth progress to a CLI status bar)."""
    global _log_callback
    _log_callback = fn

def load_tokens() -> dict:
    """Load persisted token dictionary from disk; returns {} on missing or corrupt file."""
    if TOKEN_PATH.exists():
        try:
            return json.loads(TOKEN_PATH.read_text())
        except (json.JSONDecodeError, Exception):
            pass
    return {}

def save_tokens(tokens: dict) -> None:
    """Atomically write token dict to disk with 0o600 permissions.

    Why 0o600 (owner read/write only)?  The file contains OAuth access tokens,
    refresh tokens, and client secrets — credentials that grant access to external
    APIs.  0o600 ensures only the file owner (the user running LibreAssistant) can
    read them, preventing other users or processes on a shared machine from
    exfiltrating the tokens.  The atomic write (tmp + rename) prevents partial
    writes if the process is killed mid-save.
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    tmp = TOKEN_PATH.with_suffix(".tmp")  # Atomic write: write to .tmp then rename to prevent partial writes on crash
    tmp.write_text(json.dumps(tokens, indent=2))
    os.chmod(tmp, 0o600)  # Restrict permissions to owner-only since the file contains secrets
    tmp.replace(TOKEN_PATH)

def pkce_pair() -> tuple[str, str]:
    """Generate a PKCE code_verifier and its SHA-256 code_challenge per RFC 7636.
    Why PKCE S256?  The verifier never leaves the client; only the challenge goes to
    the auth server.  Even if an attacker intercepts the auth code, they can't exchange
    it without the verifier.  This is mandatory for public clients (no client_secret)
    and recommended for all OAuth 2.0 flows.
    """
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge

def discover_oauth_endpoints(server_url: str) -> dict | None:
    """Discover OAuth 2.0 endpoints via RFC 8414 well-known metadata starting from the resource server."""
    resource_url = server_url.rstrip("/") + "/.well-known/oauth-protected-resource"  # Two-step discovery: resource server metadata -> authorization server metadata
    try:
        resp = urlopen(resource_url, timeout=10)
        meta = json.loads(resp.read().decode())
        auth_servers = meta.get("authorization_servers", [])
        if auth_servers:
            as_url = auth_servers[0].rstrip("/") + "/.well-known/oauth-authorization-server"
            as_resp = urlopen(as_url, timeout=10)
            as_meta = json.loads(as_resp.read().decode())
            return as_meta
        return meta
    except Exception:
        return None

def dcr_register(registration_url: str, redirect_uri: str) -> dict | None:
    """Register a new OAuth client via RFC 7591 Dynamic Client Registration.
    Why DCR?  MCP servers like CourtListener don't pre-assign client_ids to
    desktop apps.  DCR lets LibreAssistant register itself at runtime, receiving
    a client_id and client_secret on the fly.  The registration is persisted in
    mcp_tokens.json so subsequent sessions reuse the same client without re-registering.
    """
    body = json.dumps({
        "redirect_uris": [redirect_uri],
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "client_secret_basic",
        "client_name": "LibreAssistant",
    }).encode()  # Request a client_secret_basic client with refresh_token grant
    req = Request(registration_url, data=body, headers={"Content-Type": "application/json"})
    try:
        resp = urlopen(req, timeout=15)
        return json.loads(resp.read().decode())
    except URLError as e:
        if hasattr(e, "read"):
            try:
                err_body = json.loads(e.read().decode())
                _log_callback(f"DCR registration failed: {err_body}")
            except Exception:
                _log_callback(f"DCR registration failed (unparseable body): {e}")
        else:
            _log_callback(f"DCR registration failed (no response body): {e}")
        return None

class _RedirectHandler(BaseHTTPRequestHandler):
    """Minimal HTTP server that captures the OAuth authorization code redirect callback."""
    server: "HTTPServer"

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        params = {k: v[0] for k, v in qs.items()}
        if "code" in params or "error" in params:  # Capture auth code (or error) from query params onto the server object for the main thread
            self.server.auth_result = params
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<html><body><p>Authorization complete. You may close this tab.</p></body></html>"
            )
        else:
            self.send_response(404)

    def log_message(self, format, *args):
        pass  # Suppress default HTTP log output to stdout

def _start_local_server(host: str, port: int) -> tuple["HTTPServer", int]:
    """Start a daemon-threaded HTTP server on the given port (0 = any available) and return (server, actual_port).
    Why loopback-only (127.0.0.1)?  The redirect server only exists to capture the
    OAuth authorization code from the browser redirect.  Binding to loopback prevents
    other machines on the network from intercepting the code.  Port 0 lets the OS
    assign an available port, avoiding conflicts with other services.
    """
    server = HTTPServer((host, port), _RedirectHandler)
    server.auth_result = None
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    actual_port = server.server_address[1]
    return server, actual_port

def _wait_for_redirect(server: "HTTPServer", timeout: int = 120) -> dict:
    """Block until the redirect handler receives an auth code or the timeout expires.

    Why 120 seconds?  The user needs to open a browser, log in (possibly with 2FA),
    and authorize the app.  2 minutes covers slow logins without timing out on
    deliberate user action, while still failing promptly if the redirect never arrives
    (e.g. wrong redirect_uri, browser closed without authorizing).
    """
    deadline = time.time() + timeout
    while time.time() < deadline and server.auth_result is None:
        time.sleep(0.5)  # Poll every 500ms — avoids tight spin and keeps latency acceptable
    server.shutdown()
    if server.auth_result is None:
        raise TimeoutError("OAuth authorization timed out (2 minutes)")
    return server.auth_result

def exchange_code(
    token_url: str, client_id: str, client_secret: str | None,
    code: str, redirect_uri: str, code_verifier: str,
) -> dict:
    """Exchange the authorization code for tokens at the token endpoint."""
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "code_verifier": code_verifier,
    }
    if client_secret:
        data["client_secret"] = client_secret
    body = urllib.parse.urlencode(data).encode()
    req = Request(token_url, data=body,
                  headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        resp = urlopen(req, timeout=15)
        result = json.loads(resp.read().decode())
    except URLError as e:
        # On HTTP error, try to extract a structured error_description from the response body
        if hasattr(e, "read"):
            try:
                body = json.loads(e.read().decode())
                if "error" in body:
                    raise Exception(
                        f"Token exchange failed: {body['error']}: {body.get('error_description', '')}"
                    )
            except Exception:
                pass
        raise Exception(f"Token exchange failed: {e}")
    if "error" in result:
        raise Exception(f"Token exchange failed: {result['error']}: {result.get('error_description', '')}")
    return result

def refresh_access_token(
    token_url: str, client_id: str, client_secret: str | None, refresh: str,
) -> dict | None:
    """Refresh an expired access token; returns None on failure (caller falls through to full re-auth)."""
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh,
        "client_id": client_id,
    }
    if client_secret:
        data["client_secret"] = client_secret
    body = urllib.parse.urlencode(data).encode()
    req = Request(token_url, data=body,
                  headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        resp = urlopen(req, timeout=15)
        return json.loads(resp.read().decode())
    except URLError:
        return None  # Silently return None — the caller decides whether to fall through to interactive auth

def refresh_server_token(server_name: str, entry: dict) -> str | None:
    """Try refreshing the access token using stored credentials. Returns the new access_token on success, None on failure.

    Why extract this as a shared function?  Token refresh is needed in two places:
    (1) MCPClient._ensure_auth() checks expiry and refreshes before each request, and
    (2) authenticate_server() refreshes as a fallback before prompting for interactive auth.
    Extracting the logic here avoids duplicating the refresh + save-to-disk logic across
    both callers, and ensures the token file stays consistent regardless of which path
    triggered the refresh.
    """
    refresh = entry.get("refresh_token")
    if not refresh:
        return None
    result = refresh_access_token(
        entry.get("token_url", ""),
        entry.get("client_id", ""),
        entry.get("client_secret"),
        refresh,
    )
    if not result or "access_token" not in result:
        return None
    entry["access_token"] = result["access_token"]
    if "refresh_token" in result:
        entry["refresh_token"] = result["refresh_token"]
    if "expires_in" in result:
        entry["expires_at"] = time.time() + result["expires_in"]
    tokens = load_tokens()
    tokens[server_name] = entry
    save_tokens(tokens)
    return result["access_token"]

def authenticate_server(server_name: str, server_url: str, oauth_config: dict, force: bool = False) -> str | None:
    """Full OAuth 2.0 PKCE flow: 1) cached token, 2) refresh, 3) browser redirect + code exchange. Returns access_token or None.

    The 3-phase structure (cache → refresh → interactive) is ordered by user
    disruption: cached tokens need no action, refresh tokens need no browser, and
    only the final phase opens a browser and prompts the user.  This minimizes
    interruptions — most requests resolve in phase 1 or 2.

    The CSRF `state` parameter (line 332) prevents cross-site request forgery:
    an attacker could craft a link that auto-submits an authorization response to
    the loopback server.  By verifying that the returned state matches what we sent,
    we ensure the response came from a browser session that we initiated.
    """
    tokens = load_tokens()
    entry = tokens.get(server_name, {})

    now = time.time()

    # Check cached token (skip if force=True)  # Phase 1 — return cached token if still valid (>60s buffer)
    if not force:
        access_token = entry.get("access_token")
        expires_at = entry.get("expires_at", 0)
        if access_token and isinstance(expires_at, (int, float)) and expires_at > now + 60:
            return access_token

    # Try refresh if expired or forced  # Phase 2 — try refresh_token grant before prompting the user
    access_token = entry.get("access_token")
    if access_token and entry.get("refresh_token"):
        result = refresh_server_token(server_name, entry)
        if result:
            return result

    # Need to do full OAuth flow  # Phase 3 — full interactive OAuth 2.0 PKCE flow
    dcr = oauth_config.get("dcr", False)
    client_id = oauth_config.get("client_id") or entry.get("client_id")
    client_secret = oauth_config.get("client_secret") or entry.get("client_secret")
    auth_url = oauth_config.get("auth_url") or entry.get("auth_url")
    token_url = oauth_config.get("token_url") or entry.get("token_url")
    scopes = oauth_config.get("scopes", [])

    meta = discover_oauth_endpoints(server_url) if (not auth_url or not token_url or (dcr and not client_id)) else None  # Discover endpoints from well-known metadata only if needed (not hardcoded in config)
    if meta:
        auth_url = auth_url or meta.get("authorization_endpoint")
        token_url = token_url or meta.get("token_endpoint")

    if not auth_url or not token_url:
        return None

    # Start local server FIRST to determine port; DCR registration below needs the exact redirect_uri.
    code_verifier, code_challenge = pkce_pair()
    state = secrets.token_urlsafe(16)

    host = "127.0.0.1"

    # Try to reuse cached redirect_uri port so DCR registration stays valid
    cached_redirect_uri = entry.get("redirect_uri")
    cached_port = None
    if cached_redirect_uri:
        parsed = urllib.parse.urlparse(cached_redirect_uri)
        cached_port = parsed.port  # Reuse previously registered redirect_uri port to keep DCR registration valid across restarts

    if cached_port:
        try:
            server, actual_port = _start_local_server(host, cached_port)
        except OSError:
            # Port in use since last session — invalidate DCR client so it re-registers with the new port
            if dcr:
                client_id = None
                client_secret = None
            server, actual_port = _start_local_server(host, 0)
    else:
        server, actual_port = _start_local_server(host, 0)

    redirect_uri = f"http://{host}:{actual_port}/"

    # Phase 4 — Dynamic Client Registration now that we know the exact redirect_uri port
    if dcr and not client_id:
        reg_url = (
            (meta and meta.get("registration_endpoint"))
            or oauth_config.get("registration_url")
        )
        if reg_url:
            reg_result = dcr_register(reg_url, redirect_uri)
            if reg_result and isinstance(reg_result, dict):
                client_id = reg_result.get("client_id")
                client_secret = reg_result.get("client_secret")
                auth_url = auth_url or reg_result.get("authorization_endpoint")
                token_url = token_url or reg_result.get("token_endpoint")

    # Neither config nor DCR produced a client_id — cannot proceed
    if not client_id:
        raise Exception(
            "OAuth client_id is not configured and DCR registration failed. "
            "Check the server's registration endpoint or configure client_id manually."
        )

    params = urllib.parse.urlencode({  # Build authorization URL with PKCE parameters per RFC 7636 and OAuth 2.0 Security BCP
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": " ".join(scopes),
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
    })
    full_auth_url = f"{auth_url}?{params}"

    _log_callback(f"__AUTH_BOX__\n{server_name}\n{full_auth_url}")  # Emit machine-parsable auth signal for the CLI status bar to detect
    opened = False
    try:
        opened = webbrowser.open(full_auth_url)
    except Exception:
        pass
    if not opened:  # Fallback: xdg-open for headless/Linux environments where webbrowser.open returns False
        try:
            subprocess.Popen(["xdg-open", full_auth_url],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
    _log_callback("Waiting for authorization (up to 2 minutes)...")

    qs = _wait_for_redirect(server)

    if qs.get("state") != state:  # CSRF protection: state parameter must match what we sent in the auth request
        raise Exception("OAuth state mismatch — possible CSRF attack")

    if qs.get("error"):
        raise Exception(f"OAuth error: {qs.get('error')}: {qs.get('error_description', '')}")

    code = qs.get("code")
    if not code:
        raise Exception("No authorization code received")

    result = exchange_code(token_url, client_id, client_secret, code, redirect_uri, code_verifier)

    if "access_token" not in result:
        raise Exception(f"Token exchange did not return an access_token: {result}")
    access_token = result["access_token"]
    expires_in = result.get("expires_in", 3600)
    refresh = result.get("refresh_token")

    tokens[server_name] = {  # Persist tokens plus all metadata needed for future refresh and DCR reuse
        "access_token": access_token,
        "refresh_token": refresh,
        "expires_at": now + expires_in,
        "client_id": client_id,
        "client_secret": client_secret,
        "auth_url": auth_url,
        "token_url": token_url,
        "redirect_uri": redirect_uri,
    }
    save_tokens(tokens)
    _log_callback(f"__AUTH_OK__\n{server_name}")  # Emit machine-parsable success signal for the CLI status bar
    return access_token
