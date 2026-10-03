"""WhatsApp Cloud API webhook gateway. See docs/gateway/whatsapp.md."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from paperclip.app import Paperclip
from paperclip.gateway.cli import _observer
from paperclip.integrations import IntegrationState, IntegrationStatus


def _send_message(token: str, phone_number_id: str, to: str, text: str) -> bool:
    import httpx

    url = f"https://graph.facebook.com/v21.0/{phone_number_id}/messages"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": text}}
    try:
        resp = httpx.post(url, json=payload, headers=headers, timeout=15)
        resp.raise_for_status()
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"(whatsapp) send failed: {exc}")
        return False


def _build_handler(
    token: str,
    phone_number_id: str,
    verify_token: str,
    app_secret: str,
    allowed: str,
):
    from paperclip.config import load_settings
    from paperclip.db import connect

    s = load_settings()
    s.ensure_home()
    paperclip = Paperclip(settings=s, conn=connect(s.home, check_same_thread=False))
    paperclip.session.session_id = "whatsapp"
    paperclip_lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def _set_json(self, code: int) -> None:
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path != "/webhook":
                self._set_json(404)
                self.wfile.write(b"{}")
                return

            params = parse_qs(parsed.query)
            mode = params.get("hub.mode", [None])[0]
            challenge = params.get("hub.challenge", [None])[0]
            incoming_token = params.get("hub.verify_token", [None])[0]

            if mode == "subscribe" and incoming_token == verify_token and challenge:
                print("(whatsapp) webhook verified")
                self._set_json(200)
                self.wfile.write(challenge.encode())
            else:
                print(f"(whatsapp) verification failed: mode={mode} token={incoming_token}")
                self._set_json(403)
                self.wfile.write(b"forbidden")

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path != "/webhook":
                self._set_json(404)
                self.wfile.write(b"{}")
                return

            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)

            sig = self.headers.get("X-Hub-Signature-256", "")
            expected = "sha256=" + hmac.new(
                app_secret.encode(), body, hashlib.sha256
            ).hexdigest()
            if not hmac.compare_digest(sig, expected):
                print("(whatsapp) rejected: bad signature")
                self._set_json(403)
                self.wfile.write(b"{}")
                return

            try:
                data = json.loads(body)
            except Exception:
                self._set_json(400)
                self.wfile.write(b"bad json")
                return

            self._set_json(200)
            self.wfile.write(b"{}")

            for entry in data.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    for msg in value.get("messages", []):
                        sender = msg.get("from", "")
                        text = msg.get("text", {}).get("body", "")

                        if not text or not sender:
                            continue
                        if allowed and sender != allowed:
                            print(f"(whatsapp) rejected message from {sender} (not allowed)")
                            continue

                        print(f"you › [{sender}] {text}")
                        with paperclip_lock:
                            result = paperclip.respond(
                                text, observer=_observer, source="whatsapp"
                            )
                        print(f"paperclip › {result.reply}")

                        _send_message(
                            token, phone_number_id, sender, result.reply or "(no reply)"
                        )

    return Handler


def main() -> None:
    try:
        import httpx  # noqa: F401
    except ImportError:
        raise SystemExit("WhatsApp extra not installed: pip install 'paperclip-agent[whatsapp]'")

    from paperclip.config import load_settings

    settings = load_settings()
    token = settings.whatsapp_token
    phone_number_id = settings.whatsapp_phone_number_id
    verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
    app_secret = os.getenv("WHATSAPP_APP_SECRET", "")
    allowed = os.getenv("WHATSAPP_ALLOWED_PHONE", "")

    if not token:
        raise SystemExit(
            "Set WHATSAPP_TOKEN in .env (Meta Cloud API access token). "
            "See docs/gateway/whatsapp.md for setup."
        )
    if not phone_number_id:
        raise SystemExit(
            "Set WHATSAPP_PHONE_NUMBER_ID in .env (from WhatsApp > Getting Started page)."
        )
    if not verify_token:
        raise SystemExit(
            "Set WHATSAPP_VERIFY_TOKEN in .env (any random string you'll enter in Meta's dashboard)."
        )
    if not app_secret:
        raise SystemExit(
            "Set WHATSAPP_APP_SECRET in .env (from your app's Settings → Basic → App Secret). "
            "Required to verify webhook signatures."
        )

    handler = _build_handler(token, phone_number_id, verify_token, app_secret, allowed)
    server = ThreadingHTTPServer(("0.0.0.0", 5000), handler)
    print("WhatsApp gateway → listening on http://0.0.0.0:5000")
    print("  Webhook URL: http://<your-public-url>/webhook")
    print("  Ctrl-C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


class WhatsAppHandle:
    def __init__(self, server: ThreadingHTTPServer, thread: threading.Thread) -> None:
        self.server, self.thread = server, thread

    def stop(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        if self.thread.is_alive():
            self.thread.join(timeout=10)

    def status(self) -> IntegrationStatus:
        if not self.thread.is_alive():
            return IntegrationStatus(IntegrationState.ERROR, "gateway stopped unexpectedly")
        return IntegrationStatus(IntegrationState.CONNECTED)


def start_in_background() -> WhatsAppHandle | None:
    from paperclip.config import load_settings

    settings = load_settings()
    token = settings.whatsapp_token
    phone_number_id = settings.whatsapp_phone_number_id
    verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
    app_secret = os.getenv("WHATSAPP_APP_SECRET", "")

    if not token or not phone_number_id or not verify_token or not app_secret:
        return None
    try:
        import httpx  # noqa: F401
    except ImportError:
        print("(whatsapp) WHATSAPP_TOKEN is set but the extra isn't installed — "
              "pip install 'paperclip-agent[whatsapp]'")
        return None

    allowed = os.getenv("WHATSAPP_ALLOWED_PHONE", "")
    handler = _build_handler(token, phone_number_id, verify_token, app_secret, allowed)
    server = ThreadingHTTPServer(("0.0.0.0", 5000), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True, name="whatsapp-webhook")
    thread.start()
    return WhatsAppHandle(server, thread)


if __name__ == "__main__":
    main()
