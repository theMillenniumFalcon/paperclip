"""CLI entry. See docs/main.md."""

from __future__ import annotations

import sys


def main() -> None:
    args = sys.argv[1:]
    if not args:
        from paperclip.gateway.cli import main as cli_main

        cli_main()
    elif args[0] == "api":
        from paperclip.ops.api import main as api_main

        api_main()
    elif args[0] == "voice":
        from paperclip.gateway.voice import main as voice_main

        voice_main()
    elif args[0] == "telegram":
        from paperclip.gateway.telegram import main as tg_main

        tg_main()
    elif args[0] == "brief":
        from paperclip.ops.brief import main as brief_main

        brief_main()
    elif args[0] == "skill" and len(args) >= 3 and args[1] == "install":
        from paperclip.memory.procedural.installer import install

        install(args[2])
    else:
        print("Usage: paperclip [api|voice|telegram|brief|skill install <url>]")
        sys.exit(1)


if __name__ == "__main__":
    main()
