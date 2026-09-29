"""Telegram long-polling gateway. See docs/gateway/telegram.md."""

from __future__ import annotations

import asyncio
import os
import threading

from paperclip.app import Paperclip
from paperclip.gateway.cli import _observer
from paperclip.gateway.runner import GatewayAgentRunner, run_gateway_turn
from paperclip.integrations import IntegrationState, IntegrationStatus


def _allowed_ids() -> set[str]:
    return {p.strip() for p in os.getenv("TELEGRAM_ALLOWED_USER", "").split(",") if p.strip()}


def posture() -> str:
    ids = _allowed_ids()
    if ids:
        return f"  reachable by: {len(ids)} allowlisted user(s)"
    return ("  reachable by: ANYONE who finds this bot — it will answer from your\n"
            "                personal memory. Set TELEGRAM_ALLOWED_USER to lock it.")


def _new_runner() -> GatewayAgentRunner:
    return GatewayAgentRunner(
        Paperclip, session_id="telegram", source="telegram", observer=_observer
    )


def _build_app(token: str, allowed: str = "", runner: GatewayAgentRunner | None = None):
    allowed_ids = _allowed_ids() | ({allowed.strip()} if allowed.strip() else set())
    from telegram import Update
    from telegram.ext import Application, ContextTypes, MessageHandler, filters

    runner = runner or _new_runner()

    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if allowed_ids and str(update.effective_user.id) not in allowed_ids:
            await update.message.reply_text("This Paperclip serves someone else. Run your own!")
            return
        await run_gateway_turn(runner, update.message.text, update.message.reply_text)

    app = Application.builder().token(token).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    return app


def main() -> None:
    try:
        import telegram  # noqa: F401
    except ImportError:
        raise SystemExit("Telegram extra not installed: pip install 'paperclip-agent[telegram]'")

    from paperclip.config import load_settings

    token = load_settings().telegram_token
    if not token:
        raise SystemExit("Set TELEGRAM_BOT_TOKEN in .env (message @BotFather to create a bot).")
    runner = _new_runner()
    try:
        app = _build_app(token, runner=runner)
        print("Paperclip is listening on Telegram — message your bot. Ctrl-C to stop.")
        print(posture())
        app.run_polling()
    finally:
        runner.close()


class TelegramHandle:
    def __init__(self, loop, app, thread, conflict, runner: GatewayAgentRunner) -> None:
        self.loop, self.app, self.thread, self._conflict = loop, app, thread, conflict
        self.runner = runner

    def stop(self) -> None:
        async def shutdown():
            if self.app.updater.running:
                await self.app.updater.stop()
            if self.app.running:
                await self.app.stop()
            await self.app.shutdown()

        try:
            if self.thread.is_alive() and self.loop.is_running():
                try:
                    asyncio.run_coroutine_threadsafe(shutdown(), self.loop).result(timeout=10)
                finally:
                    if self.loop.is_running():
                        self.loop.call_soon_threadsafe(self.loop.stop)
            if self.thread.is_alive():
                self.thread.join(timeout=10)
        finally:
            self.runner.close()

    def status(self) -> IntegrationStatus:
        if self._conflict["conflict"]:
            return IntegrationStatus(IntegrationState.ERROR, "another instance is polling this token")
        if not self.thread.is_alive():
            return IntegrationStatus(IntegrationState.ERROR, "gateway stopped unexpectedly")
        if error := self.runner.error_status:
            return IntegrationStatus(IntegrationState.ERROR, error)
        return IntegrationStatus(IntegrationState.CONNECTED)


def start_in_background() -> TelegramHandle | None:
    from paperclip.config import load_settings

    token = load_settings().telegram_token
    if not token:
        return None
    try:
        import telegram  # noqa: F401
    except ImportError:
        print("(telegram) TELEGRAM_BOT_TOKEN is set but the extra isn't installed — "
              "pip install 'paperclip-agent[telegram]'")
        return None

    print("(telegram) starting:")
    print(posture())

    import logging

    warned = {"conflict": False}

    def on_poll_error(exc: Exception) -> None:
        from telegram.error import Conflict

        if isinstance(exc, Conflict) and not warned["conflict"]:
            warned["conflict"] = True
            print("(telegram) another instance is already running this bot — the dashboard's "
                  "Telegram stays idle. Stop the other `paperclip telegram` and restart to use it here.")

    loop = asyncio.new_event_loop()
    runner = _new_runner()
    try:
        app = _build_app(token, runner=runner)
    except Exception:
        runner.close()
        raise

    def run() -> None:
        logging.getLogger("telegram").setLevel(logging.CRITICAL)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(app.initialize())
            loop.run_until_complete(app.start())
            loop.run_until_complete(app.updater.start_polling(error_callback=on_poll_error))
            loop.run_forever()
        except Exception as exc:
            print(f"(telegram) background poller stopped: {exc}")

    thread = threading.Thread(target=run, daemon=True, name="telegram-poll")
    thread.start()
    return TelegramHandle(loop, app, thread, warned, runner)


if __name__ == "__main__":
    main()
