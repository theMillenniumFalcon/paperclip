"""Reset PAPERCLIP_HOME to a curated demo state. See docs/scripts/demo-seed.md."""

from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from paperclip.config import load_settings
from paperclip.db import connect
from paperclip.memory.episodic.store import SqliteEpisodeStore
from paperclip.memory.semantic.store import SqliteFactStore
from paperclip.tools.calendar import make_tool

# Curated seed — clean, no duplicates. Edit these to taste before recording.
FACTS = [
    ("user", "The user is a software engineer from India who builds web applications, "
             "AI-powered products, and developer tools. He has worked at Upsurge Labs "
             "on bhindi.io, led development of OpenBio, interned at multiple companies, "
             "and built projects using Next.js, AI APIs, databases, and modern web technologies. "
             "He shares his work through GitHub and his personal portfolio at nishank.vercel.app."),

    ("projects", "The user enjoys constantly building things, especially AI-powered applications, "
                 "full-stack web projects, and developer tools. Some of his projects include "
                 "medcare-ai, safewatch-ai, book2playlist, recipes-ai, and smolDB."),

    ("movies", "The user is a movie enthusiast who uses Letterboxd to log, rate, and review films. "
               "He prefers concise reviews, usually two to three lines, and likes getting "
               "10 variations when brainstorming a review. He generally prefers reviews that "
               "match the movie's tone rather than sarcastic one-liners."),

    ("learning", "The user is interested in AI and machine learning, backend engineering, "
                 "system design, cloud deployment, and building scalable applications. "
                 "He has explored RAG, embeddings, vector databases, multi-agent systems, "
                 "and deployment platforms such as Cloudflare."),

    ("tech", "The user works across Windows and macOS development environments, uses Bun "
             "for JavaScript projects, and has experience with Next.js, Tailwind CSS, "
             "MongoDB, PostgreSQL, Redis, and Supabase.")
]

EPISODE = (
    "2026-10-22",
    "Spent time exploring AI projects and software development ideas, "
    "with a focus on building practical applications."
)

EVENT = {
    "title": "Movie night",
    "start": "2026-10-24T19:00",
    "end": "2026-10-24T22:00",
    "attendees": "user"
}


def main(reset_spend: bool = False) -> None:
    settings = load_settings()
    home = settings.home

    if home.exists():
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = home.with_name(f"{home.name}.bak-{stamp}")
        shutil.copytree(home, backup)
        print(f"backed up {home} -> {backup}")
        # calendar.ics + these dirs are plain files no process holds open.
        # traces/ = the Loop & Tools history; clear it so those tabs start empty.
        (home / "calendar.ics").unlink(missing_ok=True)
        for sub in ("outbox", "skills", "traces"):
            d = home / sub
            if d.exists():
                shutil.rmtree(d)
        # Ops eval history — start empty so a live `make gate` adds a visible row.
        (home / "eval_runs.jsonl").unlink(missing_ok=True)
        (home / "eval_report.json").unlink(missing_ok=True)
        # The spend ledger is a permanent record — only wiped on explicit request.
        if reset_spend:
            (home / "usage.jsonl").unlink(missing_ok=True)

    settings.ensure_home()
    conn = connect(home)

    # Clear the DB rows IN PLACE — never delete state.db. Deleting the file
    # would leave any live gateway (a running `make telegram`, the dashboard,
    # an open CLI) holding a broken, read-only connection to the old inode.
    for table in ("chat_log", "calendar_events", "facts", "episodes"):
        conn.execute(f"DELETE FROM {table}")   # triggers keep the FTS index in sync
    conn.commit()

    facts, episodes = SqliteFactStore(conn), SqliteEpisodeStore(conn)
    for subject, content in FACTS:
        facts.add(subject, content, source="user")
    episodes.add(EPISODE[1], happened_at=EPISODE[0])

    create_event = make_tool(conn, home).fn
    print(create_event(**EVENT))

    # regenerate the human-readable MEMORY.md mirror for the fresh state
    from paperclip.memory import Memory

    Memory(conn, settings, None).export_markdown()

    print(f"\nclean demo state ready in {home}")
    print(f"  facts: {len(FACTS)}  ·  episodes: 1  ·  events: 1  ·  chat log: cleared")
    print("  CLEARED: loop/tool traces, Ops eval history, outbox, skills.")
    if reset_spend:
        print("  CLEARED: usage.jsonl (money/token spend) — you approved this.")
    else:
        print("  KEPT: SOUL.md and usage.jsonl (your real spend — pass --reset-spend to wipe).")
    print("  Run `python -m paperclip dashboard` and start filming.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reset PAPERCLIP_HOME to a clean demo state.")
    parser.add_argument("--reset-spend", action="store_true",
                        help="also wipe usage.jsonl (the money/token spend ledger)")
    args = parser.parse_args()
    main(reset_spend=args.reset_spend)
