"""OAuth for remote MCP: storage, browser, loopback callback. See docs/tools/mcp-oauth.md."""

from __future__ import annotations

import asyncio
import json
import os
import socket
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread
from typing import ClassVar
from urllib.parse import parse_qs, urlparse

from mcp.client.auth import OAuthClientProvider, TokenStorage
from mcp.shared.auth import (
    AuthorizationCodeResult,
    OAuthClientInformationFull,
    OAuthClientMetadata,
    OAuthToken,
)

AUTH_DIR = "mcp-auth"
CALLBACK_PORT = 41765
CALLBACK_PATH = "/callback"
SIGN_IN_TIMEOUT = 300.0


def _sanitise(name: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in name)[:64]


class FileTokenStorage(TokenStorage):
    def __init__(self, home: Path, server_name: str) -> None:
        self._path = Path(home) / AUTH_DIR / f"{_sanitise(server_name)}.json"

    def _read(self) -> dict:
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _write(self, data: dict) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        os.chmod(tmp, 0o600)
        tmp.replace(self._path)

    async def get_tokens(self):
        raw = self._read().get("tokens")
        return OAuthToken.model_validate(raw) if raw else None

    async def set_tokens(self, tokens) -> None:
        data = self._read()
        data["tokens"] = tokens.model_dump(mode="json", exclude_none=True)
        self._write(data)

    async def get_client_info(self):
        raw = self._read().get("client_info")
        return OAuthClientInformationFull.model_validate(raw) if raw else None

    async def set_client_info(self, client_info) -> None:
        data = self._read()
        data["client_info"] = client_info.model_dump(mode="json", exclude_none=True)
        self._write(data)


class _CallbackHandler(BaseHTTPRequestHandler):
    result: ClassVar[dict] = {}

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path != CALLBACK_PATH:
            self.send_response(404)
            self.end_headers()
            return
        params = parse_qs(parsed.query)
        _CallbackHandler.result = {k: v[0] for k, v in params.items()}
        body = (
            b"<html><body style='font-family:system-ui;padding:3rem'>"
            b"<h2>Signed in.</h2><p>You can close this tab and return to the terminal.</p>"
            b"</body></html>"
        )
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args) -> None:
        return


def _port_is_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def build_provider(server_url: str, server_name: str, home: Path) -> OAuthClientProvider:
    redirect_uri = f"http://127.0.0.1:{CALLBACK_PORT}{CALLBACK_PATH}"

    metadata = OAuthClientMetadata(
        client_name="Paperclip",
        redirect_uris=[redirect_uri],
        grant_types=["authorization_code", "refresh_token"],
        response_types=["code"],
        token_endpoint_auth_method="none",
    )

    async def redirect_handler(authorization_url: str) -> None:
        print("\n  Opening your browser to sign in…")
        print(f"  If it does not open: {authorization_url}\n")
        webbrowser.open_new_tab(authorization_url)

    async def callback_handler() -> AuthorizationCodeResult:
        if not _port_is_free(CALLBACK_PORT):
            raise RuntimeError(
                f"port {CALLBACK_PORT} is in use — the sign-in redirect has nowhere to land. "
                "Close whatever holds it and try again."
            )
        _CallbackHandler.result = {}
        server = HTTPServer(("127.0.0.1", CALLBACK_PORT), _CallbackHandler)
        thread = Thread(target=server.handle_request, daemon=True)
        thread.start()
        for _ in range(int(SIGN_IN_TIMEOUT / 0.5)):
            if _CallbackHandler.result:
                break
            await asyncio.sleep(0.5)
        server.server_close()

        result = _CallbackHandler.result
        if not result:
            raise RuntimeError("timed out waiting for the browser sign-in to come back")
        if "error" in result:
            raise RuntimeError(
                f"authorization failed: {result['error']}"
                + (f" — {result['error_description']}" if "error_description" in result else "")
            )
        return AuthorizationCodeResult(
            code=result["code"], state=result.get("state"), iss=result.get("iss")
        )

    return OAuthClientProvider(
        server_url=server_url,
        client_metadata=metadata,
        storage=FileTokenStorage(home, server_name),
        redirect_handler=redirect_handler,
        callback_handler=callback_handler,
    )
