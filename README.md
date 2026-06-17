# Revolution1 Skills

Reusable AI agent skills for developer and infrastructure workflows, packaged for the [skills CLI](https://www.skills.sh/docs/cli) and the [skills.sh](https://www.skills.sh/) ecosystem.

## Repository layout

```text
skills/
  <skill-name>/
    SKILL.md          # required — frontmatter + instructions
    agents/           # optional — agent-specific interface definitions
      openai.yaml
skills.sh.json        # skills.sh repository page grouping
scripts/
  validate_skills.py  # structural validator (no external dependencies)
```

Conventions:

- one folder per skill
- a required `SKILL.md` with YAML frontmatter (`name`, `description`) in each skill folder
- optional `agents/` subdirectory for agent-specific interface definitions
- `skills.sh.json` at the repo root to group skills on the skills.sh repository page

## Included skills

| Skill                                                                                | Description                                                                                                                                                                               |
| ------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`cross-repo-harness`](skills/cross-repo-harness/SKILL.md)                           | Operate related repositories through a lightweight harness repo with inventory, boundaries, sync commands, records, owner routing, target-repo PRs, and verification.                     |
| [`dev-machine-migration`](skills/dev-machine-migration/SKILL.md)                     | Migrate high-value developer data between machines or Coder workspaces. Runs in explicit phases: inventory → preflight → manifest → confirm → dry-run → copy → verify.                    |
| [`enterprise-infrastructure-osint`](skills/enterprise-infrastructure-osint/SKILL.md) | Authorized external attack-surface mapping. Guides passive DNS enumeration, CT log mining, port scanning, frontend stack fingerprinting, API extraction, and confidence-tiered reporting. |
| [`remote-chrome-devtools`](skills/remote-chrome-devtools/SKILL.md)                   | Diagnose Chrome DevTools MCP/CDP on remote Linux, covering desktop/VNC, headless Chrome, no saved MCP config, missing Chrome, and Docker browser fallbacks.                               |

## Validation

Run the included validator to check skill structure, `agents/openai.yaml`, and `skills.sh.json` references:

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
- `agents/openai.yaml` interface fields when present
- `skills.sh.json` groups only reference skills that exist in this repo

## Usage

Install skills with the `skills` CLI:

```bash
npx skills add Revolution1/skills --agent codex --global --yes
```

List skills from this repository before installing:

```bash
npx skills add Revolution1/skills --list
```

Install one skill by name:

```bash
npx skills add Revolution1/skills --skill cross-repo-harness --agent codex --global --yes
```

You can also install from a local checkout:

```bash
npx skills add . --skill cross-repo-harness --agent codex --global --yes
```

Use a skill without installing it:

```bash
npx skills use Revolution1/skills@cross-repo-harness
```

Manual fallback: copy the desired skill folder into your agent skills directory, or vendor it into your own repository.

Example (VS Code Copilot):

```bash
cp -R skills/dev-machine-migration ~/.vscode/skills/
```

## skills.sh discovery

skills.sh discovers GitHub-hosted skills through anonymous telemetry from the `skills` CLI. After this repository is installed with `npx skills add Revolution1/skills`, its skills become eligible to appear in skills.sh search, leaderboard, and repository pages after the cache refreshes.

The root [`skills.sh.json`](skills.sh.json) file controls only how the repository page is grouped on skills.sh. It does not change how the CLI installs skills or how `SKILL.md` files are interpreted.

Useful checks:

```bash
npx skills add . --list
npx skills add Revolution1/skills --list
```

## Design notes

These skills are written to be:

- shareable in public repositories
- free of machine-specific secrets
- practical for real developer-ops and infrastructure workflows
