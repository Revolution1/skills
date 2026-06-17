# Revolution1 Skills

Reusable AI agent skills for developer and infrastructure workflows, compatible with VS Code Copilot agent customization and OpenAI agent interfaces.

## Repository layout

```text
skills/
  <skill-name>/
    SKILL.md          # required — frontmatter + instructions
    agents/           # optional — agent-specific interface definitions
      openai.yaml
scripts/
  validate_skills.py  # structural validator (no external dependencies)
```

Conventions:

- one folder per skill
- a required `SKILL.md` with YAML frontmatter (`name`, `description`) in each skill folder
- optional `agents/` subdirectory for agent-specific interface definitions

## Included skills

| Skill                                                                                | Description                                                                                                                                                                               |
| ------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`cross-repo-harness`](skills/cross-repo-harness/SKILL.md)                           | Operate related repositories through a lightweight harness repo with inventory, boundaries, sync commands, records, owner routing, target-repo PRs, and verification.                     |
| [`dev-machine-migration`](skills/dev-machine-migration/SKILL.md)                     | Migrate high-value developer data between machines or Coder workspaces. Runs in explicit phases: inventory → preflight → manifest → confirm → dry-run → copy → verify.                    |
| [`enterprise-infrastructure-osint`](skills/enterprise-infrastructure-osint/SKILL.md) | Authorized external attack-surface mapping. Guides passive DNS enumeration, CT log mining, port scanning, frontend stack fingerprinting, API extraction, and confidence-tiered reporting. |
| [`remote-chrome-devtools`](skills/remote-chrome-devtools/SKILL.md)                   | Diagnose Chrome DevTools MCP/CDP on remote Linux, covering desktop/VNC, headless Chrome, no saved MCP config, missing Chrome, and Docker browser fallbacks.                               |

## Validation

Run the included validator to check skill structure:

```bash
python3 scripts/validate_skills.py
```

The validator checks each skill for:

- presence of `SKILL.md`
- valid YAML frontmatter with `name` and `description` fields
- `name` matching the directory name
- description of sufficient length to guide agent triggering
- file length under 500 lines
- presence of a top-level Markdown heading

## Usage

Install skills with the `skills` CLI:

```bash
npx skills add Revolution1/skills --agent codex --global
```

List skills from this repository before installing:

```bash
npx skills add Revolution1/skills --list
```

Install one skill by name:

```bash
npx skills add Revolution1/skills --skill cross-repo-harness --agent codex --global
```

You can also install from a local checkout:

```bash
npx skills add . --skill cross-repo-harness --agent codex --global
```

Manual fallback: copy the desired skill folder into your agent skills directory, or vendor it into your own repository.

Example (VS Code Copilot):

```bash
cp -R skills/dev-machine-migration ~/.vscode/skills/
```

## Design notes

These skills are written to be:

- shareable in public repositories
- free of machine-specific secrets
- practical for real developer-ops and infrastructure workflows
