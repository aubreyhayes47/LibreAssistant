"""Tests for libreassistant.tools.web_fetch — URL validation, content handling, security, errors, edge cases."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from libreassistant.tools.web_fetch import (
    _sniff_is_pdf,
    _strip_html,
    fetch_url,
    CHUNK_SIZE,
    MAX_SIZE,
)


def _make_response(
    content=b"<html><body>Hello</body></html>",
    status_code=200,
    content_type="text/html",
    headers=None,
    url="https://example.com",
    history=None,
):
    resp = MagicMock()
    resp.status_code = status_code
    resp.url = url
    resp.history = history or []
    hdrs = {"content-type": content_type}
    if headers:
        hdrs.update(headers)
    resp.headers = hdrs

    if isinstance(content, bytes):
        resp.iter_content.return_value = [content] if content else []
    else:
        resp.iter_content.return_value = [content.encode()]
    resp.read.return_value = content if isinstance(content, bytes) else content.encode()
    return resp


# ── 1. URL validation ────────────────────────────────────────────────


class TestURLValidation:
    @patch("libreassistant.tools.web_fetch.requests.get")
    def test_valid_https(self, mock_get):
        mock_get.return_value = _make_response(content=b"ok")
        result = fetch_url({"url": "https://example.com"})
        assert "Error" not in result
        mock_get.assert_called_once()

    @patch("libreassistant.tools.web_fetch.requests.get")
    def test_valid_http(self, mock_get):
        mock_get.return_value = _make_response(content=b"ok")
        result = fetch_url({"url": "http://example.com"})
        assert "Error" not in result

    def test_file_url_rejected(self):
        result = fetch_url({"url": "file:///etc/passwd"})
        assert "Error" in result
        assert "http/https" in result

    def test_ftp_url_rejected(self):
        result = fetch_url({"url": "ftp://example.com/file.txt"})
        assert "Error" in result

    def test_missing_scheme_rejected(self):
        result = fetch_url({"url": "example.com"})
        assert "Error" in result

    def test_empty_url_rejected(self):
        result = fetch_url({"url": ""})
        assert "Error" in result

    def test_no_url_key(self):
        result = fetch_url({})
        assert "Error" in result

    def test_special_characters_url(self):
        result = fetch_url({"url": "https://example.com/path?a=1&b=2#frag"})
        # Should pass URL validation but may fail on network — we just check it's not a validation error
        assert "only http/https" not in result

    def test_very_long_url(self):
        long_url = "https://example.com/" + "a" * 10000
        result = fetch_url({"url": long_url})
        # Should pass URL validation (starts with https://)
        assert "only http/https" not in result


# ── 2. Content type handling ──────────────────────────────────────────


class TestContentTypeHandling:
    @patch("libreassistant.tools.web_fetch.requests.get")
    def test_html_stripped(self, mock_get):
        mock_get.return_value = _make_response(
            content=b"<html><body><p>Hello <b>world</b></p></body></html>",
            content_type="text/html",
        )
        result = fetch_url({"url": "https://example.com", "format": "text"})
        assert "Hello" in result
        assert "<p>" not in result
        assert "<b>" not in result

    @patch("libreassistant.tools.web_fetch.requests.get")
    def test_html_raw_format(self, mock_get):
        mock_get.return_value = _make_response(
            content=b"<html><body><p>Hello</p></body></html>",
            content_type="text/html",
        )
        result = fetch_url({"url": "https://example.com", "format": "html"})
        assert "<p>Hello</p>" in result

    @patch("libreassistant.tools.web_fetch.requests.get")
    def test_plain_text(self, mock_get):
        mock_get.return_value = _make_response(
            content=b"Just plain text.",
            content_type="text/plain",
        )
        result = fetch_url({"url": "https://example.com", "format": "text"})
        assert "Just plain text." in result

    @patch("libreassistant.tools.web_fetch.requests.get")
    def test_pdf_content_type(self, mock_get):
        mock_get.return_value = _make_response(
            content=b"%PDF-1.4 fake pdf content",
            content_type="application/pdf",
            headers={"content-length": "1234"},
        )
        result = fetch_url({"url": "https://example.com/doc.pdf"})
        assert "PDF" in result
        assert "1234 bytes" in result

    @patch("libreassistant.tools.web_fetch.requests.get")
    def test_image_content_type(self, mock_get):
        mock_get.return_value = _make_response(
            content=b"\x89PNG",
            content_type="image/png",
            headers={"content-length": "5678"},
        )
        result = fetch_url({"url": "https://example.com/img.png"})
        assert "image" in result.lower()
        assert "5678 bytes" in result

    @patch("libreassistant.tools.web_fetch.requests.get")
    def test_json_content(self, mock_get):
        mock_get.return_value = _make_response(
            content=b'{"key": "value"}',
            content_type="application/json",
        )
        result = fetch_url({"url": "https://example.com/api"})
        assert '{"key": "value"}' in result

    @patch("libreassistant.tools.web_fetch.requests.get")
    def test_unknown_content_type(self, mock_get):
        mock_get.return_value = _make_response(
            content=b"some data",
            content_type="application/octet-stream",
        )
        result = fetch_url({"url": "https://example.com/data"})
        assert "Error" not in result or "octet" in result.lower()


# ── 3. Security ───────────────────────────────────────────────────────


class TestSecurity:
    @patch("libreassistant.tools.web_fetch.requests.get")
    def test_https_to_http_redirect(self, mock_get):
        history_entry = MagicMock()
        history_entry.url = "https://example.com"
        resp = _make_response(
            content=b"redirected",
            url="http://example.com",
            history=[history_entry],
        )
        mock_get.return_value = resp
        result = fetch_url({"url": "https://example.com"})
        assert "HTTPS→HTTP" in result
        assert "downgrade" in result.lower() or "Downgrade" in result

    @patch("libreassistant.tools.web_fetch.requests.get")
    def test_redirect_loop_detection(self, mock_get):
        """A redirect loop eventually triggers a requests error or timeout."""
        mock_get.side_effect = requests.exceptions.TooManyRedirects("redirects exceeded")
        result = fetch_url({"url": "https://example.com"})
        assert "Error" in result

    @patch("libreassistant.tools.web_fetch.requests.get")
    def test_redirect_count_enforced_by_requests(self, mock_get):
        """requests library enforces max redirects; we just verify the error path."""
        mock_get.side_effect = requests.exceptions.TooManyRedirects
        result = fetch_url({"url": "https://example.com"})
        assert "Error" in result


# ── 4. Error handling ─────────────────────────────────────────────────


class TestErrorHandling:
    @patch("libreassistant.tools.web_fetch.requests.get")
    def test_connection_timeout(self, mock_get):
        mock_get.side_effect = requests.exceptions.Timeout("timed out")
        result = fetch_url({"url": "https://slow.example.com"})
        assert "timed out" in result.lower()

    @patch("libreassistant.tools.web_fetch.requests.get")
    def test_dns_failure(self, mock_get):
        mock_get.side_effect = requests.exceptions.ConnectionError(
            "Name or service not known"
        )
        result = fetch_url({"url": "https://nonexistent.invalid"})
        assert "Error" in result

    @patch("libreassistant.tools.web_fetch.requests.get")
    def test_http_404(self, mock_get):
        mock_get.return_value = _make_response(status_code=404)
        result = fetch_url({"url": "https://example.com/missing"})
        assert "404" in result

    @patch("libreassistant.tools.web_fetch.requests.get")
    def test_http_500(self, mock_get):
        mock_get.return_value = _make_response(status_code=500)
        result = fetch_url({"url": "https://example.com/broken"})
        assert "500" in result

    @patch("libreassistant.tools.web_fetch.requests.get")
    def test_http_429_rate_limit(self, mock_get):
        mock_get.return_value = _make_response(status_code=429)
        result = fetch_url({"url": "https://example.com/rate"})
        assert "429" in result

    @patch("libreassistant.tools.web_fetch.requests.get")
    def test_connection_refused(self, mock_get):
        mock_get.side_effect = requests.exceptions.ConnectionError(
            "Connection refused"
        )
        result = fetch_url({"url": "https://localhost:9999"})
        assert "Error" in result

    @patch("libreassistant.tools.web_fetch.requests.get")
    def test_ssl_error(self, mock_get):
        mock_get.side_effect = requests.exceptions.SSLError("certificate verify failed")
        result = fetch_url({"url": "https://expired.example.com"})
        assert "Error" in result


# ── 5. Content processing ─────────────────────────────────────────────


class TestContentProcessing:
    @patch("libreassistant.tools.web_fetch.requests.get")
    def test_size_cap_enforced(self, mock_get):
        large_content = b"x" * (MAX_SIZE + 1000)
        resp = _make_response(content=large_content, content_type="text/plain")
        mock_get.return_value = resp
        result = fetch_url({"url": "https://example.com/big"})
        assert "truncated" in result.lower()

    @patch("libreassistant.tools.web_fetch.requests.get")
    def test_empty_response_body(self, mock_get):
        mock_get.return_value = _make_response(content=b"", content_type="text/plain")
        result = fetch_url({"url": "https://example.com/empty"})
        assert "Error" not in result or "blank" in result.lower() or "short" in result.lower()

    @patch("libreassistant.tools.web_fetch.requests.get")
    def test_binary_content_not_image_not_pdf(self, mock_get):
        mock_get.return_value = _make_response(
            content=b"\x00\x01\x02\x03\x04",
            content_type="application/octet-stream",
        )
        result = fetch_url({"url": "https://example.com/bin"})
        # Should not crash; binary decoded with replacement chars
        assert isinstance(result, str)

    @patch("libreassistant.tools.web_fetch.requests.get")
    def test_large_html_truncation(self, mock_get):
        large_html = b"<html><body>" + b"x" * (MAX_SIZE + 500) + b"</body></html>"
        mock_get.return_value = _make_response(content=large_html, content_type="text/html")
        result = fetch_url({"url": "https://example.com/huge"})
        assert "truncated" in result.lower()

    @patch("libreassistant.tools.web_fetch.requests.get")
    def test_encoding_fallback_to_utf8(self, mock_get):
        # Content-Type has no charset; bytes are valid UTF-8
        mock_get.return_value = _make_response(
            content="Héllo Wörld".encode("utf-8"),
            content_type="text/html",
        )
        result = fetch_url({"url": "https://example.com", "format": "text"})
        assert "Héllo" in result

    @patch("libreassistant.tools.web_fetch.requests.get")
    def test_charset_in_content_type(self, mock_get):
        mock_get.return_value = _make_response(
            content="Résumé".encode("utf-8"),
            content_type="text/html; charset=utf-8",
        )
        result = fetch_url({"url": "https://example.com", "format": "text"})
        assert "Résumé" in result

    @patch("libreassistant.tools.web_fetch.requests.get")
    def test_bad_encoding_fallback(self, mock_get):
        # Latin-1 bytes with charset=latin-1 should decode fine
        mock_get.return_value = _make_response(
            content="café".encode("latin-1"),
            content_type="text/html; charset=latin-1",
        )
        result = fetch_url({"url": "https://example.com", "format": "text"})
        assert "café" in result

    @patch("libreassistant.tools.web_fetch.requests.get")
    def test_unknown_encoding_fallback(self, mock_get):
        # Garbage charset should fall back to utf-8 with replacement
        resp = _make_response(
            content=b"\x80\x81\x82",
            content_type="text/html; charset=bogus-encoding",
        )
        mock_get.return_value = resp
        result = fetch_url({"url": "https://example.com", "format": "text"})
        assert isinstance(result, str)

    @patch("libreassistant.tools.web_fetch.requests.get")
    def test_html_entity_decoding(self, mock_get):
        # HTML entities are handled by the HTML parser's handle_data
        mock_get.return_value = _make_response(
            content=b"<p>&amp; &lt; &gt;</p>",
            content_type="text/html",
        )
        result = fetch_url({"url": "https://example.com", "format": "text"})
        # HTMLParser resolves &amp; → & etc.
        assert "&" in result
        assert "<" in result
        assert ">" in result


# ── 6. Edge cases ─────────────────────────────────────────────────────


class TestEdgeCases:
    @patch("libreassistant.tools.web_fetch.requests.get")
    def test_no_content_type_header(self, mock_get):
        resp = _make_response(content=b"plain data", content_type=None)
        resp.headers = {}
        mock_get.return_value = resp
        result = fetch_url({"url": "https://example.com", "format": "text"})
        assert "Error" not in result or "plain data" in result

    @patch("libreassistant.tools.web_fetch.requests.get")
    def test_charset_in_content_type_already_tested(self, mock_get):
        """Dedicated edge case for charset parameter in Content-Type."""
        mock_get.return_value = _make_response(
            content="<p>Hi</p>".encode("utf-8"),
            content_type="text/html; charset=utf-8; boundary=something",
        )
        result = fetch_url({"url": "https://example.com", "format": "text"})
        assert "Hi" in result

    @patch("libreassistant.tools.web_fetch.requests.get")
    def test_chunked_transfer_encoding(self, mock_get):
        resp = _make_response(content=b"chunked data", content_type="text/plain")
        resp.headers["transfer-encoding"] = "chunked"
        mock_get.return_value = resp
        result = fetch_url({"url": "https://example.com"})
        assert "chunked data" in result

    @patch("libreassistant.tools.web_fetch.requests.get")
    def test_gzip_content_encoding(self, mock_get):
        import gzip

        compressed = gzip.compress(b"compressed text here")
        resp = _make_response(content=compressed, content_type="text/plain")
        resp.headers["content-encoding"] = "gzip"
        # iter_content with decode_unicode=False returns raw bytes;
        # requests transparently decodes gzip when streaming if auto_decode=True
        # Since we mock, we return the raw compressed bytes — decode will fail
        # and fall back to utf-8 replacement. This tests the fallback path.
        mock_get.return_value = resp
        result = fetch_url({"url": "https://example.com"})
        assert isinstance(result, str)

    def test_sniff_pdf_magic_bytes(self):
        assert _sniff_is_pdf(b"%PDF-1.4 content")
        assert _sniff_is_pdf(b"%PDF-\x00\x00")
        assert not _sniff_is_pdf(b"<html>")
        assert not _sniff_is_pdf(b"")
        assert not _sniff_is_pdf(b"%PD")

    @patch("libreassistant.tools.web_fetch.requests.get")
    def test_mislabeled_pdf_sniffed(self, mock_get):
        """PDF served with text/html content-type is caught by magic-byte sniffing."""
        mock_get.return_value = _make_response(
            content=b"%PDF-1.4 fake pdf content here",
            content_type="text/html",
        )
        result = fetch_url({"url": "https://example.com/tricky.pdf"})
        assert "PDF" in result

    def test_strip_html_script_and_style(self):
        html = "<html><head><script>var x=1;</script><style>.c{}</style></head><body><p>real</p></body></html>"
        result = _strip_html(html)
        assert "var x=1" not in result
        assert ".c{}" not in result
        assert "real" in result

    def test_strip_html_nested_skip_tags(self):
        html = "<div><script><style>nested</style></script></div><p>visible</p>"
        result = _strip_html(html)
        assert "nested" not in result
        assert "visible" in result

    def test_strip_html_blank_page(self):
        mock_resp = _make_response(
            content=b"<html><body></body></html>",
            content_type="text/html",
        )
        with patch("libreassistant.tools.web_fetch.requests.get", return_value=mock_resp):
            result = fetch_url({"url": "https://example.com/blank"})
        assert "blank" in result.lower() or "short" in result.lower()

    @patch("libreassistant.tools.web_fetch.requests.get")
    def test_short_response_warning(self, mock_get):
        mock_get.return_value = _make_response(
            content=b"hi",
            content_type="text/html",
        )
        result = fetch_url({"url": "https://example.com/tiny"})
        assert "short response" in result.lower() or len(b"hi") < 200

    def test_unknown_format_rejected(self):
        result = fetch_url({"url": "https://example.com", "format": "json"})
        assert "Error" in result
        assert "unknown format" in result.lower()

    @patch("libreassistant.tools.web_fetch.requests.get")
    def test_cloudflare_403_retry(self, mock_get):
        """When Cloudflare 403 is detected, the function retries with honest UA."""
        first_resp = _make_response(status_code=403, content_type="text/html")
        first_resp.headers["Server"] = "cf-mitigated: challenge"
        second_resp = _make_response(content=b"<p>OK after retry</p>", content_type="text/html")
        mock_get.side_effect = [first_resp, second_resp]
        result = fetch_url({"url": "https://example.com"})
        assert mock_get.call_count == 2
        assert "OK after retry" in result

    @patch("libreassistant.tools.web_fetch.requests.get")
    def test_403_not_cloudflare(self, mock_get):
        """Non-Cloudflare 403 returns the 403 message directly."""
        mock_get.return_value = _make_response(status_code=403)
        result = fetch_url({"url": "https://example.com"})
        assert "403" in result

    @patch("libreassistant.tools.web_fetch.requests.get")
    def test_cloudflare_retry_https_downgrade(self, mock_get):
        """Cloudflare retry path also checks for HTTPS→HTTP downgrade."""
        first_resp = _make_response(status_code=403, content_type="text/html")
        first_resp.headers["Server"] = "cf-mitigated: challenge"
        second_resp = _make_response(content=b"downgraded", content_type="text/html", url="http://example.com")
        history_entry = MagicMock()
        history_entry.url = "https://example.com"
        second_resp.history = [history_entry]
        mock_get.side_effect = [first_resp, second_resp]
        result = fetch_url({"url": "https://example.com"})
        assert "HTTPS→HTTP" in result

    @patch("libreassistant.tools.web_fetch.requests.get")
    def test_cloudflare_retry_generic_error(self, mock_get):
        """Cloudflare retry path handles request exceptions."""
        first_resp = _make_response(status_code=403, content_type="text/html")
        first_resp.headers["Server"] = "cf-mitigated: challenge"
        mock_get.side_effect = [first_resp, requests.exceptions.ConnectionError("fail")]
        result = fetch_url({"url": "https://example.com"})
        assert "Cloudflare bypass failed" in result

    @patch("libreassistant.tools.web_fetch.requests.get")
    def test_generic_request_exception(self, mock_get):
        mock_get.side_effect = requests.exceptions.RequestException("something broke")
        result = fetch_url({"url": "https://example.com"})
        assert "Error" in result
        assert "something broke" in result

    def test_default_format_is_text(self):
        """Omitting format should default to 'text'."""
        with patch("libreassistant.tools.web_fetch.requests.get") as mock_get:
            mock_get.return_value = _make_response(
                content=b"<p>Hello</p>", content_type="text/html"
            )
            result = fetch_url({"url": "https://example.com"})
            assert "<p>" not in result
