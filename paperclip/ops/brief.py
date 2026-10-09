"""Morning brief into the outbox. See docs/ops/brief.md."""

from __future__ import annotations

from datetime import date

from rich.console import Console

from paperclip.app import Paperclip

PROMPT = "Brief me on my week: what's on my calendar, what's in my mail that needs attention, and what I should focus on today."


def main() -> None:
    console = Console()
    paperclip = Paperclip()
    if not paperclip.settings.apple_tools:
        console.print("[dim]Tip: set PAPERCLIP_APPLE_TOOLS=1 to brief from your real Calendar and Mail.[/dim]")
    result = paperclip.respond(PROMPT, source="brief")
    console.print(result.reply)
    out = paperclip.settings.home / "outbox" / f"brief-{date.today().isoformat()}.txt"
    out.write_text(result.reply + "\n")
    console.print(f"[dim]saved to {out}[/dim]")


if __name__ == "__main__":
    main()
