"""Connect hosted Paperclip Memory over MCP. See docs/tools/paperclip-memory.md."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

NAME = "paperclip_memory"
URL = "https://paperclip-api.vercel.app/mcp"
DOCS = "https://www.paperclip.one/docs"


def _has_mcp() -> bool:
    return importlib.util.find_spec("mcp") is not None


def add_server(home: Path) -> tuple[str, dict]:
    """Returns (status, spec): added | present | conflict."""
    config = home / "mcp.json"
    data = json.loads(config.read_text(encoding="utf-8")) if config.exists() else {}
    servers = data.setdefault("servers", [])

    for spec in servers:
        if spec.get("url", "").rstrip("/") == URL:
            return "present", spec
    for spec in servers:
        if spec.get("name") == NAME:
            return "conflict", spec

    spec = {"name": NAME, "url": URL, "oauth": True}
    servers.append(spec)
    home.mkdir(parents=True, exist_ok=True)
    config.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return "added", spec


def status(home: Path) -> str:
    config = home / "mcp.json"
    try:
        servers = json.loads(config.read_text(encoding="utf-8")).get("servers", []) if config.exists() else []
    except json.JSONDecodeError:
        return f"not connected · {config} is not valid JSON"
    spec = next((s for s in servers if s.get("url", "").rstrip("/") == URL), None)
    if spec is None:
        return "not connected · run: paperclip connect paperclip-memory"
    if spec.get("auth_env"):
        return f"configured · API key in ${spec['auth_env']}"
    if not _has_mcp():
        return "configured · needs the mcp extra: pip install 'paperclip-agent[mcp]'"

    from paperclip.tools.mcp_cli import _auth_file, _identity

    token = _auth_file(home, spec["name"])
    if not token.exists():
        return "configured · not signed in: run paperclip connect paperclip-memory"
    return f"connected · {_identity(token)}"


def connect(home: Path) -> str:
    if not _has_mcp():
        return ("Paperclip Memory connects over MCP, which needs an extra: "
                "pip install 'paperclip-agent[mcp]' (in a checkout: pip install -e '.[mcp]'). "
                "Then run this again.")

    status, spec = add_server(home)
    name, config = spec["name"], home / "mcp.json"
    if status == "conflict":
        return (f"'{name}' in {config} already points at {spec.get('url')}, not {URL}. "
                "Change it there if you meant the hosted Paperclip Memory.")

    done = {"added": f"Added Paperclip Memory to {config}. ",
            "present": ""}[status]
    elsewhere = f"To use the same memory in Claude Code, Codex or Grok Bot: {DOCS}"

    if spec.get("auth_env"):
        return (f"{done}Paperclip Memory is set up as '{name}', using the API key in "
                f"${spec['auth_env']}. Restart Paperclip to load its tools. {elsewhere}")

    from paperclip.tools.mcp_cli import _auth_file, _identity, sign_in

    token = _auth_file(home, name)
    if token.exists() and status == "present":
        return (f"Paperclip Memory is already connected as {_identity(token)}. "
                f"To switch accounts: paperclip mcp login {name}. {elsewhere}")

    ok, message = sign_in(home, name)
    if not ok:
        return f"{done}{message.strip()} Help: {DOCS}"
    return (f"{done}Connected to Paperclip Memory as {_identity(token)}. "
            f"Restart Paperclip to load its tools (paperclip_memory_*). {elsewhere}")
