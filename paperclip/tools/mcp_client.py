"""MCP bridge: sync loop ↔ async MCP SDK. See docs/tools/mcp-client.md."""

from __future__ import annotations

import asyncio
import json
import os
import re
import threading
from contextlib import AsyncExitStack
from pathlib import Path

from paperclip.tools.registry import Tool


def _model_safe_name(server: str, tool: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9_-]", "_", f"{server}_{tool}")
    if len(safe) <= 64:
        return safe
    return safe[-64:].lstrip("_")


def _auth_hint(spec: dict, auth_dir: Path) -> str:
    if spec.get("oauth"):
        return (
            f"  {spec['url']} — sign-in did not complete. Run paperclip again to use a token "
            f"that was saved, or delete {auth_dir} to start over"
        )
    return (
        f"  {spec['url']} — if the server requires auth, check that "
        f"{spec.get('auth_env') or 'auth_env'} holds a current credential"
    )


class MCPBridge:
    def __init__(self, config_path: Path, timeout: float = 30.0):
        self.config_path = config_path
        self.timeout = timeout
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._stack: AsyncExitStack | None = None
        self._sessions: dict = {}

    def _deadline(self, servers: list[dict]) -> float:
        from paperclip.tools.mcp_oauth import SIGN_IN_TIMEOUT

        if any(s.get("oauth") and not self._token_exists(s) for s in servers):
            return SIGN_IN_TIMEOUT + 60.0
        return self.timeout * 2

    def start(self) -> list[Tool]:
        self._thread.start()
        servers = json.loads(self.config_path.read_text(encoding="utf-8")).get("servers", [])
        fut = asyncio.run_coroutine_threadsafe(self._connect_all(servers), self._loop)
        listed = fut.result(self._deadline(servers))
        tools: list[Tool] = []
        for srv, metas in listed.items():
            for meta in metas:
                tools.append(Tool(
                    name=_model_safe_name(srv, meta["name"]),
                    description=f"[MCP:{srv}] {meta.get('description','') or ''}",
                    input_schema=meta.get("inputSchema") or {"type": "object", "properties": {}},
                    fn=(lambda srv=srv, tname=meta["name"], **kw: self.call(srv, tname, kw)),
                ))
        return tools

    async def _open_streams(self, spec: dict):
        from mcp import StdioServerParameters
        from mcp.client.stdio import stdio_client

        url = spec.get("url")
        if url and spec.get("command"):
            raise ValueError("server has both 'url' and 'command' — pick one transport")

        if not url:
            params = StdioServerParameters(
                command=spec["command"], args=spec.get("args", []), env=spec.get("env") or None
            )
            return await self._stack.enter_async_context(stdio_client(params))

        from mcp.client.streamable_http import create_mcp_http_client, streamable_http_client

        headers = {}
        auth = None
        auth_env = spec.get("auth_env")
        use_oauth = bool(spec.get("oauth"))

        if auth_env and use_oauth:
            raise ValueError("server names both 'auth_env' and 'oauth' — pick one")

        if auth_env:
            token = os.environ.get(auth_env)
            if not token:
                raise ValueError(f"{auth_env} is not set (named by 'auth_env' in mcp.json)")
            headers["Authorization"] = f"Bearer {token}"
        elif use_oauth:
            from paperclip.tools.mcp_oauth import build_provider

            auth = build_provider(url, spec["name"], self.config_path.parent)

        client = await self._stack.enter_async_context(
            create_mcp_http_client(headers=headers, auth=auth)
        )
        return await self._stack.enter_async_context(
            streamable_http_client(url, http_client=client)
        )

    def _token_exists(self, spec: dict) -> bool:
        if not spec.get("oauth"):
            return False
        from paperclip.tools.mcp_oauth import FileTokenStorage

        return FileTokenStorage(self.config_path.parent, spec["name"])._path.exists()

    async def _connect_one(self, spec: dict) -> list[dict]:
        from mcp import ClientSession

        name = spec["name"]
        read, write = await self._open_streams(spec)
        session = await self._stack.enter_async_context(ClientSession(read, write))
        await session.initialize()
        self._sessions[name] = session
        tools = (await session.list_tools()).tools
        return [
            {
                "name": t.name,
                "description": t.description,
                "inputSchema": getattr(t, "input_schema", None) or getattr(t, "inputSchema", None),
            }
            for t in tools
        ]

    async def _connect_all(self, servers) -> dict:
        self._stack = AsyncExitStack()
        listed: dict = {}
        for spec in servers:
            name = spec["name"]
            had_token = self._token_exists(spec)
            try:
                listed[name] = await self._connect_one(spec)
            except Exception as first_exc:
                error = first_exc
                if not had_token and self._token_exists(spec):
                    print(f"  signed in — reconnecting to '{name}'")
                    try:
                        listed[name] = await self._connect_one(spec)
                        continue
                    except Exception as retry_exc:
                        error = retry_exc

                print(f"MCP server '{name}' failed to connect: {error}")
                if spec.get("url") and not isinstance(error, ValueError):
                    print(_auth_hint(spec, self.config_path.parent / "mcp-auth"))
        return listed

    def call(self, server: str, tool: str, args: dict) -> str:
        try:
            fut = asyncio.run_coroutine_threadsafe(self._acall(server, tool, args), self._loop)
            return fut.result(self.timeout)
        except Exception as exc:
            return f"MCP call {server}_{tool} failed: {exc}"

    async def _acall(self, server: str, tool: str, args: dict) -> str:
        session = self._sessions.get(server)
        if session is None:
            return f"MCP server '{server}' is not connected."
        result = await session.call_tool(tool, args)
        parts = []
        for block in result.content:
            parts.append(getattr(block, "text", None) or "[non-text content]")
        return "\n".join(parts) or "(no output)"

    def close(self) -> None:
        if self._stack is not None:
            try:
                asyncio.run_coroutine_threadsafe(self._stack.aclose(), self._loop).result(10)
            except Exception:
                pass
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=5)
