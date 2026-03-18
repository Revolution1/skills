# Revolution1 Skills

Reusable Codex-compatible skills for developer workflows.

## Repository layout

```text
skills/
  <skill-name>/
    SKILL.md
```

This layout keeps the repo compatible with common public skill-sharing conventions:
- one folder per skill
- a required `SKILL.md` in each skill folder
- optional future expansion to `agents/`, `scripts/`, `references/`, and `assets/`

## Included skills

- `skills/dev-machine-migration` — migrate useful developer data between machines or workspaces while avoiding rebuildable bulk.

## Usage

Copy the desired skill folder into your Codex skills directory, or vendor it into your own repository.

Example:

```bash
cp -R skills/dev-machine-migration "$CODEX_HOME/skills/"
```

## Design notes

These skills are written to be:
- shareable in public repositories
- free of machine-specific secrets
- practical for real migration and developer-ops workflows
