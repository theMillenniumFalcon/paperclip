"""Read-only Google Calendar. See docs/tools/google-calendar.md."""

from __future__ import annotations

import datetime as _dt
from pathlib import Path

READONLY_SCOPE = "https://www.googleapis.com/auth/calendar.events.readonly"
DEFAULT_SCOPES = [READONLY_SCOPE]
TIMEOUT = 30

BUNDLED_CLIENT_CONFIG = {
    "installed": {
        "client_id": "",
        "client_secret": "",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["http://localhost"],
    }
}

_INSTALL_HINT = (
    "Google Calendar support is not installed — run: pip install -e '.[gcal]'"
)
_SETUP_HINT = (
    "Google Calendar is not connected yet. Type `/connect google` in the "
    "dashboard chat, or run `paperclip connect google` in a terminal — either opens "
    "your browser to sign in."
)


def _token_path(home: Path) -> Path:
    return home / "google-token.json"


def _load_credentials(home: Path, scopes: list[str]):
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
    except ImportError:
        return None

    path = _token_path(home)
    if not path.exists():
        return None
    try:
        creds = Credentials.from_authorized_user_file(str(path), scopes=scopes)
    except Exception:
        return None
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            path.write_text(creds.to_json(), encoding="utf-8")
        except Exception:
            return None
    return creds if (creds and creds.valid) else None


def connect(home: Path) -> str:
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        return _INSTALL_HINT

    own = home / "credentials.json"
    try:
        if own.exists():
            flow = InstalledAppFlow.from_client_secrets_file(
                str(own), scopes=DEFAULT_SCOPES
            )
            client_source = "credentials.json override"
        else:
            bundled = BUNDLED_CLIENT_CONFIG.get("installed", {})
            if not bundled.get("client_id") or not bundled.get("client_secret"):
                return (
                    "Google Calendar's bundled OAuth client is not configured "
                    "yet. Add .paperclip/credentials.json to use your own Desktop "
                    "OAuth client."
                )
            flow = InstalledAppFlow.from_client_config(
                BUNDLED_CLIENT_CONFIG,
                scopes=DEFAULT_SCOPES,
            )
            client_source = "bundled OAuth client"
        creds = flow.run_local_server(port=0)
    except Exception as exc:
        return f"Google sign-in failed or was cancelled ({type(exc).__name__}). Nothing was saved."

    path = _token_path(home)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(creds.to_json(), encoding="utf-8")
    return (
        f"Google Calendar connected (read-only via {client_source}). "
        f"Token cached at {path}."
    )


def list_google_events(home: Path, start: str = "", end: str = "", limit: int = 20) -> str:
    try:
        from googleapiclient.discovery import build
    except ImportError:
        return _INSTALL_HINT

    creds = _load_credentials(home, DEFAULT_SCOPES)
    if creds is None:
        return _SETUP_HINT

    today = _dt.date.today().isoformat()
    s = (start or today)[:10]
    e = (end or s)[:10]
    tz = _dt.datetime.now().astimezone().tzinfo
    lo = _dt.datetime.fromisoformat(s).replace(tzinfo=tz)
    hi = _dt.datetime.fromisoformat(e).replace(tzinfo=tz) + _dt.timedelta(days=1)

    try:
        service = build("calendar", "v3", credentials=creds, cache_discovery=False)
        resp = service.events().list(
            calendarId="primary",
            timeMin=lo.isoformat(),
            timeMax=hi.isoformat(),
            singleEvents=True,
            orderBy="startTime",
            maxResults=max(1, min(int(limit or 20), 100)),
        ).execute()
    except Exception as exc:
        return f"Google Calendar unavailable ({type(exc).__name__}: {str(exc)[:120]})"

    items = resp.get("items", [])
    if not items:
        return f"No Google Calendar events between {s} and {e}."
    lines = []
    for ev in items:
        when = ev.get("start", {})
        at = when.get("dateTime") or when.get("date") or "?"
        who = ", ".join(a.get("email", "") for a in ev.get("attendees", []) if a.get("email"))
        lines.append(f"{ev.get('summary', '(no title)')} | {at}" + (f" | {who}" if who else ""))
    return "\n".join(lines)


def is_connected(home: Path) -> bool:
    return _token_path(home).exists()
