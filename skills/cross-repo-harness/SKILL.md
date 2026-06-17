---
name: cross-repo-harness
description: Use when creating, scaffolding, maintaining, or operating a lightweight harness repository that organizes many related repositories for one product, company, infrastructure estate, GitOps environment, or multi-component system. Guides initial repo creation, inventory design, ownership routing, permission boundaries, repo sync/update flows, target-repo changes, shared runbooks, decision/change records, local agent memory, self-evolving documentation, and live verification without converting the repos into a monorepo or submodules.
---

# Cross Repo Harness

## Overview

Use a harness repo as a tracked control plane around related repos: it indexes where things live, explains how they relate, provides repeatable local commands, and records operational decisions. Keep source changes in the target repos; keep routing data, runbooks, helper commands, and cross-repo evidence in the harness.

For new harness creation, prefer the bundled scaffold script, then tailor the
generated files after inspecting the actual target repos:

```bash
python3 <skill-dir>/scripts/scaffold_harness.py \
  --path ~/code/8004scan-harness \
  --name 8004scan-harness \
  --domain 8004scan \
  --repo backend=https://github.com/<org>/8004scan-backend.git \
  --repo frontend=https://github.com/<org>/8004scan-frontend.git
```

Use the script as a starting point, not as final truth. The finished harness
must reflect live repo evidence, owners, environments, and workflows.

## Model

A harness repo is useful when the system is too connected for isolated repos but should not become a monorepo. It should provide:

- **Inventory**: machine-readable facts about repos, owners, environments, clusters, services, domains, and permissions.
- **Locator docs**: short guidance for choosing the right repo before editing.
- **Local workspace commands**: clone/update/status helpers that operate under an ignored `repos/` directory or equivalent.
- **Boundary rules**: what may be touched from the harness, what needs a target-repo PR, and what must never be committed.
- **Operational records**: tracked decisions, changes, incidents, runbooks, and verification evidence.
- **Scratch memory**: ignored local notes and todos for operator context that should not become shared documentation.
- **Self-evolution rules**: when new durable facts or procedures are found,
  update the harness first, then optionally improve target-repo docs with a
  scoped PR.

This pattern is adjacent to multi-repo manifest tools, developer portals, and repo fleet CLIs, but the harness adds operational judgment: ownership, approval routing, live-state checks, and audit trail.

## Standard Workflow

### 1. Classify the Request

Determine whether the user is asking to:

- find the right repo or owner
- inspect live state across repos/environments
- change a target repo
- improve the harness itself
- create or update inventory/runbooks/records
- build a new harness from scattered repos

For production-facing work, inspect the live source of truth before claiming readiness. For target-repo edits, first identify the owner/reviewer path from inventory, repo history, CODEOWNERS, PR history, and user-provided context.

When creating a new harness, gather the minimum viable inputs:

- harness name and destination path
- product/system domain
- initial target repos and clone URLs
- primary environments, if known
- whether the target repos use GitHub, GitLab, local paths, or mixed remotes

If some inputs are missing, create a conservative scaffold with placeholders
and TODO notes rather than inventing facts.

### 2. Locate the Right Repo

Read the harness indexes before cloning or editing:

- app/product inventory for ownership and service routing
- infra/GitOps/Terraform inventory for deployment paths
- environment/cluster inventory for access boundaries
- repo locator or architecture docs when the target is unclear
- relevant playbooks before operational changes

If inventory is missing, stale, or vague after checking real GitHub, cluster, Flux, Rancher, cloud, or runtime state, update the harness inventory before finishing.

For a brand-new harness, inspect the initial target repos before finalizing the
inventory:

- default branches and active branches
- README/docs/runbooks
- repo-local instructions such as `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`,
  `.cursorrules`, and `.windsurfrules`
- package/workflow files that reveal build, test, release, and deploy paths
- recent commits, CODEOWNERS, and PR history for owner/reviewer hints
- deployment hints such as Dockerfiles, Helm charts, Terraform, GitOps,
  Kubernetes manifests, compose files, cloud config, or CI pipelines

### 3. Sync Only Needed Repos

Clone or update only the target repos needed for the task. Prefer a harness-provided CLI such as `./harness repo sync <name>` when present. Otherwise use a documented local convention such as:

```bash
mkdir -p repos
git clone <url> repos/<repo-name>
git -C repos/<repo-name> fetch --all --prune
```

Do not add target repos as submodules unless the harness explicitly uses submodules. Keep operational clones in an ignored directory.

### 4. Respect Write Boundaries

Separate changes by destination:

- **Target repo**: product code, Helm charts, Terraform, GitOps manifests, workflow files, app docs.
- **Harness repo**: inventory, repo locator docs, operational playbooks, helper commands, change/decision/incident records.
- **Ignored local memory**: task scratch notes, operator-specific todo lists, temporary findings.

Never commit credentials, kubeconfigs, decoded secrets, private keys, tokens, `.env` files, or rendered manifests containing secret values. When secret metadata is needed, avoid printing decoded values.

### 5. Make Target Changes in Target Repos

Before editing a target repo:

- inspect its README and nearby files
- read repo-local agent instructions such as `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.cursorrules`, `.windsurfrules`, and nested instruction files relevant to the files being changed
- confirm default/base branch and current working tree
- choose the smallest target repo scope
- preserve unrelated local changes
- run repo-local validation
- open PRs from the target repo, not the harness repo

Prefer one target repo PR per coherent operational change. Avoid broad edits across unrelated repos just because they are reachable from the harness.

### Target Repo Instructions

Do not assume managed repo instructions are automatically inherited by the harness.

Agent instruction loading is runtime-specific:

- `AGENTS.md` may be loaded automatically by some Codex environments when it is on the working path or inside the edited subtree.
- `CLAUDE.md` is a Claude Code convention and should be read explicitly when Codex is operating on that repo.
- Nested instruction files only apply safely after checking the specific directory tree being edited.
- Shell commands run with `workdir=repos/<repo>` do not by themselves prove the agent has loaded the repo's instruction file.

When a harness manages target repos, treat target-repo instruction discovery as part of routing. Read the target repo's instruction files before making edits or judging validation requirements, and mention any important target-specific rule in the final summary when it affected the work.

Target-repo instructions are scoped. They do not override the harness repo's
global instructions, inventory maintenance rules, sensitive-data handling,
permission boundaries, or shared-record requirements. If a target instruction
conflicts with the harness, use the stricter rule and record durable conflicts
in the harness.

### 6. Update the Harness as Shared Memory

When the task discovers durable infrastructure facts, repo relationships, permission constraints, safer procedures, or new recurring operations, update the harness before finishing:

- inventory entry
- locator or architecture doc
- playbook or runbook
- CLI command documentation if a repeated operation was automated
- change record for infrastructure changes
- decision record for architecture evolution, tradeoffs, and research
- incident record and external incident issue when the work is an incident or significant maintenance

Keep records factual: what changed, why, where, validation performed, remaining gaps, and rollback or follow-up where relevant.

Default knowledge placement:

- Cross-repo routing, access, ownership, agent behavior, PR flow, and shared
  operations belong in the harness.
- Repo-local commands or workflows should be summarized in the harness when
  they affect cross-repo work.
- Open a scoped PR to the target repo only when that repo's README,
  instructions, or runbooks should change for repo-local users.
- Never let target-repo instructions automatically mutate harness rules.

### 7. Verify and Report

Close with evidence from the right layer:

- target repo validation commands and results
- live runtime checks for production-facing claims
- PR URLs and review routing
- harness inventory/docs changed
- any access gap or permission boundary that prevented verification

Do not claim readiness from local manifests alone when a live cluster, deployment system, cloud resource, or production endpoint is the actual source of truth.

## Harness Structure

Adapt names to the repo, but prefer a predictable shape:

```text
inventory/
  README.md
  repos.toml
  app-repos.toml
  environments.toml
docs/
  architecture/
  operations/
  playbooks/
  records/
    changes/
    decisions/
repos/              # ignored target-repo clones
.memory/            # ignored operator notes
.todos.md           # ignored local task list
harness             # optional CLI entrypoint
scripts/
  bootstrap_repos.py
  repo_status.py
```

Use structured inventory formats such as TOML, YAML, or JSON when the data is routing-critical. Validate inventory syntax after edits.

For small app/product harnesses, `app-repos.toml` and `environments.toml` may
start minimal. Do not over-model cloud or cluster inventory before there is
evidence.

## New Harness Scaffold

When the user asks to create a harness, use this flow:

1. Run `scripts/scaffold_harness.py` from this skill with the destination,
   harness name, domain, and any known repos.
2. Initialize git only if the user asked or the destination is already a repo.
3. Clone only the needed target repos into the generated `repos/` directory.
4. Inspect target repo docs, instructions, ownership hints, build/deploy files,
   and recent commits.
5. Update generated inventory and docs with evidence-backed facts.
6. Keep `repos/`, `.memory/`, `.todos.md`, `tmp/`, and secrets ignored.
7. Validate TOML and `git diff --check`.
8. Summarize the route, generated files, known gaps, and next target repos to
   inspect.

Do not add target repos as submodules. Let users choose SSH or HTTPS remotes;
inventory should store canonical URLs and clone hints, not force one protocol
unless the organization requires it.

## CLI Guidance

Add a harness CLI command when an operation is repeated, error-prone, or needs consistent safety checks. Keep commands categorized, lazily import heavy dependencies, and document them in the harness operations docs.

Good harness commands:

- `repo sync <name>`
- `repo status [--all]`
- `inventory validate`
- `memory bootstrap`
- `todos bootstrap`
- `cluster context list`
- `record change new`
- `record decision new`

Avoid hiding dangerous production writes behind broad commands. Destructive or high-blast-radius commands should require explicit flags and should print the target environment before acting.

## Output Shape

For cross-repo work, summarize:

- **Route**: harness files read, target repo selected, owner/reviewer signal.
- **Changes**: target repo changes and harness updates separately.
- **Validation**: local checks plus live checks when relevant.
- **Records**: change/decision/incident docs or issues created/updated.
- **Gaps**: access limits, missing owners, skipped validation, or stale inventory found.
