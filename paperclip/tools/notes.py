"""save_note into the facts table. See docs/tools/notes.md."""

from __future__ import annotations

import sqlite3

from paperclip.tools.registry import Tool


def make_tool(conn: sqlite3.Connection) -> Tool:
    def save_note(subject: str, content: str) -> str:
        conn.execute(
            "INSERT INTO facts (subject, content, source) VALUES (?,?,'user')",
            (subject.lower().strip(), content),
        )
        conn.commit()
        return f"Saved to memory under '{subject}': {content}"

    return Tool(
        name="save_note",
        description=(
            "Save a durable fact to long-term memory. Use when the user tells you something "
            "worth remembering about themselves, a person, or a project — especially if they "
            "say 'remember' or share a preference."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "subject": {"type": "string", "description": "Who/what this is about, e.g. 'alex' or 'acme-project'"},
                "content": {"type": "string", "description": "The fact, one sentence"},
            },
            "required": ["subject", "content"],
        },
        fn=save_note,
    )
