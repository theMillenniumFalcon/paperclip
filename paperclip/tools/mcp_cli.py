"""paperclip mcp — list / login / logout. See docs/tools/mcp-cli.md."""

from __future__ import annotations

import base64
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

PAPERCLIP_HOME = Path(".paperclip")

_USAGE = """\
    paperclip mcp                 list servers and who you are signed in as
    paperclip mcp login <name>    sign in again — as someone else, or after expiry
    paperclip mcp logout <name>   forget the token; the next run signs in fresh
"""


def _claims(access_token: str) -> dict:
    if access_token.count(".") != 2:
        return {}
    body = access_token.split(".")[1]
    body += "=" * (-len(body) % 4)
    try:
        return json.loads(base64.urlsafe_b64decode(body))
    except Exception:
        return {}


def _identity(auth_file: Path) -> str:
    if not auth_file.exists():
        return "not signed in"
    try:
        stored = json.loads(auth_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return "unreadable — will sign in again"

    claims = _claims(stored.get("tokens", {}).get("access_token", ""))
    who = claims.get("email") or claims.get("sub") or "unknown account"

    exp = claims.get("exp")
    if not exp:
        return who
    left = datetime.fromtimestamp(exp, UTC) - datetime.now(UTC)
    if left.total_seconds() <= 0:
        return f"{who} — token expired, refreshes on next use"
    minutes = int(left.total_seconds() // 60)
    return f"{who} — {minutes // 60}h left" if minutes >= 60 else f"{who} — {minutes}m left"


def _servers(home: Path) -> list[dict]:
    config = home / "mcp.json"
    if not config.exists():
        return []
    try:
        return json.loads(config.read_text(encoding="utf-8")).get("servers", [])
    except json.JSONDecodeError as exc:
        print(f"{config} is not valid JSON: {exc}")
        raise SystemExit(1) from exc


def _auth_file(home: Path, name: str) -> Path:
    from paperclip.tools.mcp_oauth import FileTokenStorage

    return FileTokenStorage(home, name)._path


def _list(home: Path) -> int:
    servers = _servers(home)
    if not servers:
        print(f"No MCP servers configured. See docs/tools/mcp.md, or write {home}/mcp.json")
        return 0

    for spec in servers:
        name = spec["name"]
        if spec.get("url"):
            if spec.get("oauth"):
                auth = f"oauth · {_identity(_auth_file(home, name))}"
            elif spec.get("auth_env"):
                auth = f"api key · ${spec['auth_env']}"
            else:
                auth = "no credential"
            print(f"  {name}\n    {spec['url']}\n    {auth}")
        else:
            print(f"  {name}\n    {spec['command']} (local process)\n    no credential needed")
    return 0


def _logout(home: Path, name: str) -> int:
    path = _auth_file(home, name)
    if not path.exists():
        print(f"'{name}' is not signed in")
        return 0
    path.unlink()
    print(f"Signed out of '{name}'. The next run will sign in again.")
    return 0


def _login(home: Path, name: str) -> int:
    ok, message = sign_in(home, name)
    print(message)
    return 0 if ok else 1


def sign_in(home: Path, name: str) -> tuple[bool, str]:
    names = [s["name"] for s in _servers(home)]
    if name not in names:
        return False, f"No server called '{name}' in {home}/mcp.json. Configured: {', '.join(names) or 'none'}"

    path = _auth_file(home, name)
    if path.exists():
        path.unlink()

    from paperclip.tools.mcp_client import MCPBridge

    bridge = MCPBridge(home / "mcp.json")
    try:
        bridge.start()
    except TimeoutError:
        return False, ("\n  Timed out waiting for the browser sign-in.\n"
                       "  If you did finish it, `paperclip mcp` will show the account. Otherwise run this again.")
    except Exception:
        pass
    finally:
        bridge.close()

    if not path.exists():
        return False, f"\n  Sign-in did not complete — '{name}' has no token."
    return True, f"\n  {name} — {_identity(path)}"


def cli_main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[2:] if argv is None else argv)
    home = Path(PAPERCLIP_HOME)

    if not args:
        return _list(home)
    if args[0] in {"login", "logout"} and len(args) == 2:
        return (_login if args[0] == "login" else _logout)(home, args[1])

    print("Show which MCP servers are configured and who you are signed in as.\n")
    print(_USAGE)
    return 1
