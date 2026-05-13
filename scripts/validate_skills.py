#!/usr/bin/env python3
"""Validate repository skill structure without external dependencies."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "skills"
MAX_SKILL_LINES = 500


def parse_frontmatter(text: str, path: Path) -> tuple[dict[str, str], list[str]]:
    errors: list[str] = []
    if not text.startswith("---\n"):
        return {}, [f"{path}: missing YAML frontmatter"]

    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, [f"{path}: frontmatter is not closed"]

    fields: dict[str, str] = {}
    for line_no, line in enumerate(text[4:end].splitlines(), start=2):
        if not line.strip():
            continue
        if line.startswith((" ", "\t", "-")):
            errors.append(f"{path}:{line_no}: nested frontmatter is not supported by this validator")
            continue
        if ":" not in line:
            errors.append(f"{path}:{line_no}: invalid frontmatter line")
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip().strip('"').strip("'")

    return fields, errors


def validate_skill(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    skill_file = skill_dir / "SKILL.md"

    if not skill_file.exists():
        return [f"{skill_dir}: missing SKILL.md"]

    text = skill_file.read_text(encoding="utf-8")
    fields, frontmatter_errors = parse_frontmatter(text, skill_file)
    errors.extend(frontmatter_errors)

    name = fields.get("name", "")
    description = fields.get("description", "")

    if not name:
        errors.append(f"{skill_file}: missing frontmatter field 'name'")
    elif name != skill_dir.name:
        errors.append(f"{skill_file}: name '{name}' does not match directory '{skill_dir.name}'")

    if not description:
        errors.append(f"{skill_file}: missing frontmatter field 'description'")
    elif len(description.split()) < 8:
        errors.append(f"{skill_file}: description is too short to guide triggering")

    allowed_fields = {"name", "description", "metadata"}
    extra_fields = sorted(set(fields) - allowed_fields)
    if extra_fields:
        errors.append(f"{skill_file}: unexpected frontmatter field(s): {', '.join(extra_fields)}")

    line_count = len(text.splitlines())
    if line_count > MAX_SKILL_LINES:
        errors.append(f"{skill_file}: {line_count} lines exceeds {MAX_SKILL_LINES}-line guidance")

    if not re.search(r"^#\s+\S+", text, flags=re.MULTILINE):
        errors.append(f"{skill_file}: missing top-level Markdown heading")

    for readme in skill_dir.glob("README*"):
        errors.append(f"{readme}: README files do not belong inside skill directories")

    return errors


def main() -> int:
    if not SKILLS_DIR.exists():
        print(f"Missing skills directory: {SKILLS_DIR}", file=sys.stderr)
        return 1

    skill_dirs = sorted(path for path in SKILLS_DIR.iterdir() if path.is_dir())
    if not skill_dirs:
        print("No skills found.", file=sys.stderr)
        return 1

    errors: list[str] = []
    for skill_dir in skill_dirs:
        errors.extend(validate_skill(skill_dir))

    if errors:
        print("Skill validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Validated {len(skill_dirs)} skill(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
