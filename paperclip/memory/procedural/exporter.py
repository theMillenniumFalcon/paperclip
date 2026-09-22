"""Copy Paperclip skills into Claude Code / Codex folders. See docs/memory/procedural.md."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

TARGETS = {"claude": ".claude", "codex": ".codex"}


def _skills(home: Path) -> list:
    from paperclip.memory import bundled_skill_dirs
    from paperclip.memory.procedural.loader import SkillLoader

    dirs = [*bundled_skill_dirs(), home / "skills"]
    roots = {d.resolve() for d in dirs}
    by_name = {}
    for skill in SkillLoader(dirs).skills:
        folder = skill.path.parent.resolve()
        if folder in roots or "_incoming" in folder.parts:
            continue
        by_name[skill.name] = skill
    return list(by_name.values())


def _files(folder: Path) -> dict[Path, bytes]:
    return {p.relative_to(folder): p.read_bytes() for p in folder.rglob("*")
            if p.is_file() and "__pycache__" not in p.parts and p.name != ".DS_Store"}


def export(targets: list[str], home: Path, base: Path, force: bool = False) -> list[str]:
    """Copy each skill folder to base/<target>/skills/<name>/. One line per copy."""
    lines = []
    for target in targets:
        root = base / TARGETS[target] / "skills"
        for skill in _skills(home):
            src, dest = skill.path.parent, root / skill.name
            if dest.exists():
                if _files(src) == _files(dest):
                    lines.append(f"  unchanged   {dest}")
                    continue
                if not force:
                    lines.append(f"  kept yours  {dest} (it differs; --force replaces it)")
                    continue
                shutil.rmtree(dest)
            shutil.copytree(src, dest, ignore=shutil.ignore_patterns("__pycache__", ".DS_Store"))
            lines.append(f"  copied      {dest}")
    return lines


def cli_main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="paperclip skill export",
        description="Copy Paperclip's skills into another agent's skills folder.")
    parser.add_argument("--to", default="claude", help="claude, codex, or both: claude,codex")
    parser.add_argument("--project", action="store_true",
                        help="write under ./.claude or ./.codex in this folder instead of your home")
    parser.add_argument("--force", action="store_true", help="replace copies that differ")
    args = parser.parse_args(argv)

    targets = [t.strip().lower() for t in args.to.split(",") if t.strip()]
    if "memory" in targets:
        print("Exporting skills to Paperclip Memory is not available yet: Paperclip Memory is adding "
              "a place for skills first. For now: --to claude,codex")
        return 1
    unknown = [t for t in targets if t not in TARGETS]
    if unknown or not targets:
        print(f"Unknown target: {', '.join(unknown) or '(none)'}. Choose from: {', '.join(TARGETS)}")
        return 1

    from paperclip.config import load_settings

    lines = export(targets, load_settings().home, Path.cwd() if args.project else Path.home(),
                   force=args.force)
    print("\n".join(lines) if lines else "No skills found to export.")
    return 0
