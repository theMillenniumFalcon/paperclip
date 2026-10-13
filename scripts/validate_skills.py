"""Validate every repo SKILL.md. See docs/scripts/validate-skills.md."""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from paperclip.memory.procedural.loader import _parse

MAX_BODY_LINES = 80


def main() -> None:
    problems: list[str] = []
    names: dict[str, Path] = {}

    files = sorted((REPO / "skills").rglob("SKILL.md"))
    if not files:
        problems.append("no SKILL.md files found under skills/")

    for path in files:
        rel = path.relative_to(REPO)
        skill = _parse(path)
        if skill is None:
            problems.append(f"{rel}: missing/invalid frontmatter (need `name` and `description`)")
            continue
        if skill.name in names:
            problems.append(f"{rel}: duplicate name '{skill.name}' (also in {names[skill.name]})")
        names[skill.name] = rel
        if len(skill.description.split()) < 5:
            problems.append(f"{rel}: description too short to match anything — say when to use it")
        if len(skill.body.splitlines()) > MAX_BODY_LINES:
            problems.append(f"{rel}: body over {MAX_BODY_LINES} lines — skills load into the prompt, keep them tight")

    if problems:
        print("skill validation FAILED:")
        for p in problems:
            print("  -", p)
        sys.exit(1)
    print(f"skill validation OK — {len(names)} skill(s): {', '.join(sorted(names))}")


if __name__ == "__main__":
    main()
