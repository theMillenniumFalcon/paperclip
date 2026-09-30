"""Discord gateway (DM-first, deny-by-default). See docs/gateway/discord.md."""

from __future__ import annotations

import asyncio
import os
import threading
import time
from pathlib import Path

from paperclip.app import Paperclip
from paperclip.gateway.cli import _observer
from paperclip.gateway.runner import GatewayAgentRunner, run_gateway_turn
from paperclip.integrations import IntegrationState, IntegrationStatus


def _ids(env: str) -> set[str]:
    return {p.strip() for p in os.getenv(env, "").split(",") if p.strip()}


class TurnBudget:
    def __init__(self, per_hour: int) -> None:
        self.per_hour = per_hour
        self._turns: list[float] = []

    def allow(self, now: float | None = None) -> bool:
        now = time.time() if now is None else now
        self._turns = [t for t in self._turns if now - t < 3600]
        if len(self._turns) >= self.per_hour:
            return False
        self._turns.append(now)
        return True


def should_answer(*, is_dm: bool, author_id: str, channel_id: str, mentioned: bool,
                  allowed_users: set[str], allowed_channels: set[str],
                  require_mention: bool) -> bool:
    if allowed_users and author_id not in allowed_users:
        return False
    if is_dm:
        return True
    if channel_id not in allowed_channels:
        return False
    return mentioned or not require_mention


def _strip_mention(content: str, bot_id: str) -> str:
    for form in (f"<@{bot_id}>", f"<@!{bot_id}>"):
        content = content.replace(form, " ")
    return content.strip()


def _build_agent() -> Paperclip:
    home = os.getenv("DISCORD_HOME", "").strip()
    if not home:
        return Paperclip()
    from paperclip.config import load_settings

    settings = load_settings()
    settings.home = Path(home)
    settings.ensure_home()
    return Paperclip(settings=settings)


def _new_runner() -> GatewayAgentRunner:
    return GatewayAgentRunner(
        _build_agent, session_id="discord", source="discord", observer=_observer
    )


def _build_client(runner: GatewayAgentRunner | None = None):
    import discord

    allowed_users = _ids("DISCORD_ALLOWED_USER")
    allowed_channels = _ids("DISCORD_ALLOWED_CHANNEL")
    require_mention = os.getenv("DISCORD_REQUIRE_MENTION", "1").strip() not in ("", "0")
    budget = TurnBudget(int(os.getenv("DISCORD_MAX_TURNS_PER_HOUR", "30")))

    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)
    runner = runner or _new_runner()

    @client.event
    async def on_message(message: discord.Message) -> None:
        if message.author == client.user or not message.content:
            return
        if not should_answer(
            is_dm=message.guild is None,
            author_id=str(message.author.id),
            channel_id=str(message.channel.id),
            mentioned=client.user in message.mentions,
            allowed_users=allowed_users,
            allowed_channels=allowed_channels,
            require_mention=require_mention,
        ):
            return
        if not budget.allow():
            print(f"(discord) hourly turn budget spent — ignoring {message.author}")
            return
        text = _strip_mention(message.content, str(client.user.id))
        if not text:
            return
        async with message.channel.typing():
            await run_gateway_turn(runner, text, message.reply)

    return client


def describe_posture() -> str:
    users = _ids("DISCORD_ALLOWED_USER")
    channels = _ids("DISCORD_ALLOWED_CHANNEL")
    who = f"{len(users)} allowlisted user(s)" if users else "anyone who can DM it"
    where = (f"{len(channels)} allowlisted channel(s), @mention required"
             if channels else "DMs only — no server channel will be answered")
    home = os.getenv("DISCORD_HOME", "").strip() or ".paperclip — YOUR personal memory"
    cap = os.getenv("DISCORD_MAX_TURNS_PER_HOUR", "30")
    return (f"  reachable by: {who}\n"
            f"  answers in:   {where}\n"
            f"  memory:       {home}\n"
            f"  spend cap:    {cap} turns/hour")


def main() -> None:
    try:
        import discord  # noqa: F401
    except ImportError:
        raise SystemExit("Discord extra not installed: pip install 'paperclip-agent[discord]'")

    token = os.getenv("DISCORD_BOT_TOKEN", "")
    if not token:
        raise SystemExit("Set DISCORD_BOT_TOKEN in .env (create a bot in the Discord Developer Portal).")
    runner = _new_runner()
    try:
        client = _build_client(runner)
        print("Paperclip is listening on Discord. Ctrl-C to stop.")
        print(describe_posture())
        client.run(token)
    finally:
        runner.close()


class DiscordHandle:
    def __init__(self, client, thread, started, runner: GatewayAgentRunner) -> None:
        self.client, self.thread, self.started = client, thread, started
        self.runner = runner

    def stop(self) -> None:
        try:
            self.started.wait(timeout=5)
            loop = getattr(self.client, "loop", None)
            try:
                if loop and loop.is_running():
                    asyncio.run_coroutine_threadsafe(self.client.close(), loop).result(timeout=10)
            finally:
                if self.thread.is_alive():
                    self.thread.join(timeout=10)
        finally:
            self.runner.close()

    def status(self) -> IntegrationStatus:
        if not self.thread.is_alive() or self.client.is_closed():
            return IntegrationStatus(IntegrationState.ERROR, "gateway stopped unexpectedly")
        if error := self.runner.error_status:
            return IntegrationStatus(IntegrationState.ERROR, error)
        if self.client.is_ready():
            return IntegrationStatus(IntegrationState.CONNECTED)
        return IntegrationStatus(IntegrationState.INSTALLED_BUT_UNCONFIGURED, "starting")


def start_in_background() -> DiscordHandle | None:
    token = os.getenv("DISCORD_BOT_TOKEN", "")
    if not token:
        return None
    try:
        import discord  # noqa: F401
    except ImportError:
        print("(discord) DISCORD_BOT_TOKEN is set but the extra isn't installed — "
              "pip install 'paperclip-agent[discord]'")
        return None

    print("(discord) starting:")
    print(describe_posture())

    runner = _new_runner()
    try:
        client = _build_client(runner)
    except Exception:
        runner.close()
        raise
    started = threading.Event()

    @client.event
    async def on_ready():
        started.set()

    def run() -> None:
        try:
            client.run(token)
        except Exception as exc:  # noqa: BLE001
            print(f"(discord) background client stopped: {exc}")

    thread = threading.Thread(target=run, daemon=True, name="discord-client")
    thread.start()
    return DiscordHandle(client, thread, started, runner)


if __name__ == "__main__":
    main()
