#!/usr/bin/env python3
"""Validate repository skill structure without external dependencies."""

from __future__ import annotations

import re
import sys
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "skills"
SKILLS_SH_CONFIG = ROOT / "skills.sh.json"
MAX_SKILL_LINES = 500
OPENAI_YAML_REQUIRED_KEYS = ("display_name", "short_description", "default_prompt")


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

    openai_yaml = skill_dir / "agents" / "openai.yaml"
    if openai_yaml.exists():
        errors.extend(validate_openai_yaml(openai_yaml, skill_dir.name))

    return errors


def validate_openai_yaml(path: Path, skill_name: str) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")

    if not re.search(r"^interface:\s*$", text, flags=re.MULTILINE):
        return [f"{path}: missing top-level interface section"]

    values: dict[str, str] = {}
    for key in OPENAI_YAML_REQUIRED_KEYS:
        match = re.search(rf'^\s{{2}}{key}:\s*"(.*)"\s*$', text, flags=re.MULTILINE)
        if not match:
            errors.append(f"{path}: missing interface.{key} string")
            continue
        values[key] = match.group(1)

    short_description = values.get("short_description", "")
    if short_description and not 25 <= len(short_description) <= 64:
        errors.append(f"{path}: interface.short_description must be 25-64 characters")

    default_prompt = values.get("default_prompt", "")
    if default_prompt and f"${skill_name}" not in default_prompt:
        errors.append(f"{path}: interface.default_prompt must mention ${skill_name}")

    return errors


def validate_skills_sh_config(skill_names: set[str]) -> list[str]:
    if not SKILLS_SH_CONFIG.exists():
        return [f"{SKILLS_SH_CONFIG}: missing skills.sh repo-page config"]

    try:
        config = json.loads(SKILLS_SH_CONFIG.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{SKILLS_SH_CONFIG}:{exc.lineno}:{exc.colno}: invalid JSON: {exc.msg}"]

    errors: list[str] = []
    not_grouped = config.get("notGrouped", "bottom")
    if not_grouped not in {"top", "bottom"}:
        errors.append(f"{SKILLS_SH_CONFIG}: notGrouped must be 'top' or 'bottom'")

    groupings = config.get("groupings")
    if not isinstance(groupings, list) or not groupings:
        errors.append(f"{SKILLS_SH_CONFIG}: groupings must be a non-empty array")
        return errors

    for index, group in enumerate(groupings, start=1):
        if not isinstance(group, dict):
            errors.append(f"{SKILLS_SH_CONFIG}: group {index} must be an object")
            continue
        title = group.get("title")
        skills = group.get("skills")
        if not isinstance(title, str) or not title.strip():
            errors.append(f"{SKILLS_SH_CONFIG}: group {index} must have a non-empty title")
        if not isinstance(skills, list) or not skills:
            errors.append(f"{SKILLS_SH_CONFIG}: group {index} must have a non-empty skills array")
            continue
        for skill in skills:
            if not isinstance(skill, str) or not skill.strip():
                errors.append(f"{SKILLS_SH_CONFIG}: group {index} contains an invalid skill name")
            elif skill not in skill_names:
                errors.append(f"{SKILLS_SH_CONFIG}: group {index} references unknown skill '{skill}'")

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
    errors.extend(validate_skills_sh_config({path.name for path in skill_dirs}))

    if errors:
        print("Skill validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Validated {len(skill_dirs)} skill(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
