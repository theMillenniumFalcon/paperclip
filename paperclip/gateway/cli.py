"""Terminal REPL gateway. See docs/gateway/cli.md."""

from __future__ import annotations

from rich.console import Console
from rich.markup import escape
from rich.panel import Panel

from paperclip.app import Paperclip

console = Console()


def _observer(kind: str, event: dict) -> None:
    if kind == "tool":
        detail = escape(f"{event['tool']}({event['args']}) → {event['output'][:80]}")
        console.print(f"  [dim]tool · {detail}[/dim]")
    elif kind == "gate":
        console.print(
            f"  [dim]gate · {escape(str(event['decision']))} — {escape(str(event.get('reason', '')))}[/dim]"
        )
    elif kind == "consolidation":
        console.print(f"  [dim]memory · consolidated {event['new_facts']} fact(s) from recent chats[/dim]")


def main() -> None:
    paperclip = Paperclip()
    paperclip.session.session_id = "terminal"
    console.print(Panel.fit(
        "[bold]Paperclip[/bold] — local, yours, transparent.\n"
        f"home: {paperclip.settings.home.resolve()}   model: {paperclip.settings.model}\n"
        "Ctrl-D or /quit to exit.",
        border_style="cyan",
    ))
    while True:
        try:
            user_message = console.input("[bold cyan]you ›[/bold cyan] ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user_message:
            continue
        if user_message in ("/quit", "/exit"):
            break
        result = paperclip.respond(user_message, observer=_observer, source="cli")
        console.print(f"[bold green]paperclip ›[/bold green] {escape(result.reply)}\n")
    console.print("[dim]bye — your memory stays in state.db[/dim]")


if __name__ == "__main__":
    main()
