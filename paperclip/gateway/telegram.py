"""Telegram long-polling gateway. See docs/gateway/telegram.md."""

from __future__ import annotations

import asyncio
import logging
import os
import threading

from paperclip.app import Paperclip
from paperclip.config import load_settings
from paperclip.gateway.cli import _observer


def _build_app(token: str, allowed: str):
    from telegram import Update
    from telegram.ext import Application, ContextTypes, MessageHandler, filters

    paperclip = Paperclip()
    paperclip.session.session_id = "telegram"

    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if allowed and str(update.effective_user.id) != allowed:
            await update.message.reply_text("This Paperclip serves someone else. Run your own!")
            return
        print(f"you › {update.message.text}")
        result = paperclip.respond(update.message.text, observer=_observer, source="telegram")
        print(f"paperclip › {result.reply}")
        await update.message.reply_text(result.reply or "(no reply)")

    app = Application.builder().token(token).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    return app


def main() -> None:
    try:
        import telegram  # noqa: F401
    except ImportError:
        raise SystemExit("Telegram extra not installed: pip install 'paperclip[telegram]'")

    token = load_settings().telegram_token
    if not token:
        raise SystemExit("Set TELEGRAM_BOT_TOKEN in .env (message @BotFather to create a bot).")
    app = _build_app(token, os.getenv("TELEGRAM_ALLOWED_USER", ""))
    print("Paperclip is listening on Telegram — message your bot. Ctrl-C to stop.")
    app.run_polling()


def start_in_background() -> bool:
    token = load_settings().telegram_token
    if not token:
        return False
    try:
        import telegram  # noqa: F401
    except ImportError:
        print("(telegram) TELEGRAM_BOT_TOKEN is set but the extra isn't installed — "
              "pip install 'paperclip[telegram]'")
        return False

    allowed = os.getenv("TELEGRAM_ALLOWED_USER", "")
    warned = {"conflict": False}

    def on_poll_error(exc: Exception) -> None:
        from telegram.error import Conflict

        if isinstance(exc, Conflict) and not warned["conflict"]:
            warned["conflict"] = True
            print("(telegram) another instance is already running this bot — the dashboard's "
                  "Telegram stays idle. Stop the other `paperclip telegram` and restart to use it here.")

    def run() -> None:
        logging.getLogger("telegram").setLevel(logging.CRITICAL)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            app = _build_app(token, allowed)
            loop.run_until_complete(app.initialize())
            loop.run_until_complete(app.start())
            loop.run_until_complete(app.updater.start_polling(error_callback=on_poll_error))
            loop.run_forever()
        except Exception as exc:  # noqa: BLE001
            print(f"(telegram) background poller stopped: {exc}")

    threading.Thread(target=run, daemon=True, name="telegram-poll").start()
    return True


if __name__ == "__main__":
    main()
