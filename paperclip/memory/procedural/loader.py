"""Parse and match SKILL.md files. See docs/memory/procedural.md."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Skill:
    name: str
    description: str
    body: str
    path: Path


def _parse_text(text: str, path: Path) -> Skill | None:
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not match:
        return None
    front, body = match.groups()
    fields = {
        k.strip(): v.strip().strip("'\"")
        for k, _, v in (line.partition(":") for line in front.splitlines() if ":" in line)
    }
    if "name" not in fields or "description" not in fields:
        return None
    return Skill(fields["name"], fields["description"], body.strip(), path)


def _parse(path: Path) -> Skill | None:
    return _parse_text(path.read_text(encoding="utf-8"), path)


class SkillLoader:
    def __init__(self, dirs: list[Path]):
        self.dirs = dirs
        self.skills: list[Skill] = []
        self._sig: tuple = ()
        self.refresh()

    def _scan_sig(self) -> tuple:
        sig = []
        for d in self.dirs:
            if d.is_dir():
                for f in sorted(d.rglob("SKILL.md")):
                    sig.append((str(f), f.stat().st_mtime))
        return tuple(sig)

    def refresh(self) -> None:
        self.skills = []
        for d in self.dirs:
            if not d.is_dir():
                continue
            for f in sorted(d.rglob("SKILL.md")):
                skill = _parse(f)
                if skill:
                    self.skills.append(skill)
        self._sig = self._scan_sig()

    def match(self, message: str, max_skills: int = 2) -> list[Skill]:
        if self._scan_sig() != self._sig:
            self.refresh()
        msg_words = set(re.findall(r"[a-z0-9]{3,}", message.lower()))
        scored = []
        for skill in self.skills:
            skill_words = set(re.findall(r"[a-z0-9]{3,}", (skill.name + " " + skill.description).lower()))
            overlap = len(msg_words & skill_words)
            if overlap >= 2:
                scored.append((overlap, skill))
        scored.sort(key=lambda pair: -pair[0])
        return [skill for _, skill in scored[:max_skills]]
