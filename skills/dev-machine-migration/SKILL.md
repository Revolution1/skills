---
name: dev-machine-migration
description: Use when migrating useful developer data from one machine or workspace to another. Supports both Coder workspace-to-workspace migration and generic local-to-remote SSH migration. First inventory and classify files/services, then present a migration plan, manifest, and exact scripts, explicitly ask the user about include/exclude choices and whether any services should be restored, and only then perform the transfer. Prefer rsync over direct SSH for the actual migration and finish with verification.
---

# Dev Machine Migration

Migrate the smallest high-value set first. Default goal: preserve active work and user configuration without copying rebuildable bulk.

## Use this skill for

- Coder workspace → Coder workspace migration
- Local machine → remote SSH host migration
- Developer machine replacement
- Rehydrating a fresh environment from an older one
- Moving local-only state before deleting a source machine

## Core operating mode

This skill should run in explicit phases:

1. Analyze source machine
2. Run preflight checks
3. Build migration manifest and exact commands
4. Ask the user to confirm include/exclude choices and service-restore intent
5. Run a dry-run preview
6. Perform migration
7. Verify destination state

Do not jump straight into copying unless the user explicitly asks you to do so without a review step.

## Default priorities

1. Uncommitted source code and new files in git repos
2. Project-local env files and local config
3. User dotfiles and shell/editor/git/tmux config
4. Credentials and CLI config needed to resume work
5. Optional tool state only if it saves meaningful setup time
6. Runtime-service inventory to inform post-migration restoration

## Default exclusions

Do not migrate these unless the user explicitly wants them:

- `node_modules`
- `.venv`, `venv`, `site-packages`, `dist-packages`
- `.next`, `dist`, `build`, coverage outputs
- `.pytest_cache`, `.mypy_cache`, `__pycache__`
- `.terraform`
- `target/` for Rust builds
- `pkg/mod`, `vendor/` for Go modules unless explicitly needed
- package manager caches
- browser caches
- large vendored trees that can be re-fetched
- IDE extension caches and server caches
- active process state, PID files, sockets, lock files

## Required workflow

### 1. Inventory source machine

Collect:

- git repos with uncommitted changes
- project `.env*` files
- user dotfiles
- SSH, cloud, Docker, Kubernetes, GitHub CLI config
- any hand-maintained tool config directories
- currently running services and listening ports

Useful commands:

```bash
git status --short
find ~ -maxdepth 2 -type f \( -name '.zshrc' -o -name '.bashrc' -o -name '.gitconfig' -o -name '.tmux.conf' -o -name '.env' -o -name '.env.*' \)
for d in ~/code/*; do [ -d "$d/.git" ] && echo "### ${d##*/}" && git -C "$d" status --short; done
systemctl list-units --type=service --state=running
ps -eo pid,ppid,lstart,cmd
ss -lntp
```

### 2. Preflight checks

Before generating copy commands, check:

- destination SSH connectivity
- destination free disk space
- `rsync`, `ssh`, and `git` availability on both sides
- whether destination paths already exist
- whether direct SSH is really usable with the chosen key and chosen transfer primitive

Useful commands:

```bash
ssh user@host 'df -h ~ && command -v rsync && command -v git'
rsync -nav ~/some-small-file user@host:/tmp/
ssh user@host 'test -d ~/code/project && echo EXISTS'
```

### 3. Classify

Split findings into three buckets:

- **Must migrate**: uncommitted code, secrets, dotfiles, irreplaceable config
- **Optional**: tool state that saves time but is recreatable
- **Skip**: bulky rebuildable outputs

Also classify services into:

- **Destination-provided**: should already exist on the target template/host
- **Restore later**: user may want them restarted after migration
- **Record only**: useful context, but not worth restoring now

### 4. Build the migration manifest and scripts

For each path, record:

- source path
- destination path
- reason to migrate
- copy method
- whether secrets are involved
- overwrite strategy

Produce exact commands for:

- file copy
- SSH key preparation if needed
- post-copy verification
- optional service restoration

### 5. Ask before execution

Before copying, explicitly confirm with the user:

- whether to include or exclude any optional files/directories
- whether to migrate project `.env` files containing secrets
- whether any recorded services should be restored after copy
- whether to keep destination-only files untouched
- whether to preserve destination-side SSH access files such as `authorized_keys`
- whether destination repos should preserve or replace existing `.git` metadata

If the user has already answered these, restate the resolved scope briefly and proceed.

### 6. Dry-run preview

Before the real copy, show a dry-run preview whenever practical.

Preferred preview:

```bash
rsync -nav --delete-excluded ...
```

Use the dry-run to surface:

- accidental large directories
- dangerous overwrites
- unexpected secret files
- `.git` or `authorized_keys` handling mistakes

### 7. Perform migration

Default transport: **`rsync + direct SSH`**.

If the source or destination is a Coder workspace:

- ensure port 22 is reachable
- ensure the intended public key exists in destination `~/.ssh/authorized_keys`
- verify direct SSH with the exact key and exact transfer primitive before bulk copy

Fallbacks such as SSH aliases or proxy-based transport are acceptable only if direct SSH is unavailable or unreliable.

### 8. Verify after copy

Verify:

- expected files exist
- permissions on secret files remain tight
- git repos still show expected uncommitted changes
- env files are present
- shell startup and CLI config work
- direct SSH still works after syncing `~/.ssh`
- destination-only access files were not accidentally replaced

Useful checks:

```bash
ls -la ~/.ssh
stat ~/.ssh/id_ed25519
for d in ~/code/*; do [ -d "$d/.git" ] && echo "### ${d##*/}" && git -C "$d" status --short; done
```

## Manifest template

Always structure the migration summary like this:

### Must migrate
- path
- reason
- method

### Optional
- path
- reason
- default action

### Skip
- path/pattern
- reason

### Services inventory
- service/process
- owner project
- current port(s)
- classification: destination-provided / restore later / record only
- restore command if relevant

### Copy commands
- exact commands in execution order

### Verification commands
- exact commands in execution order

## Transport guidance

### Preferred

Use `rsync -a` over direct SSH.

Example:

```bash
rsync -a ~/.ssh/ user@host:~/.ssh/ --exclude authorized_keys
rsync -a ~/code/project/ user@host:~/code/project/ \
  --exclude node_modules \
  --exclude .venv \
  --exclude .next \
  --exclude __pycache__
```

### SSH key handling

Never assume destination SSH access will survive a home-directory sync.

Rules:

- Never blindly overwrite `~/.ssh/authorized_keys`
- Exclude `authorized_keys` from `~/.ssh/` syncs by default
- Merge keys instead of replacing them
- Verify the exact expected key is present before switching to direct-IP transfer
- After syncing `~/.ssh`, verify direct SSH still works

### `.git` handling

Do not leave this implicit.

Rules:

- If the user wants active development context preserved, migrate `.git` metadata for the selected repos
- If the destination already has a different checkout, ask before replacing or merging `.git`
- If the goal is only source snapshot transfer, explicitly exclude `.git`
- Default recommendation for workstation/workspace migration: **preserve `.git`** for repos containing uncommitted work

### Coder-specific note

A successful `ssh <workspace>.coder` does not prove direct-IP `ssh`, `scp`, or `rsync` will behave the same. Always test the exact primitive you plan to use.

## High-value paths to consider

User-level:

- `~/.ssh`
- `~/.gitconfig`
- `~/.bashrc`, `~/.zshrc`, `~/.profile`
- `~/.tmux.conf`
- `~/.kube`
- `~/.aws`
- `~/.docker/config.json`
- `~/.config/gcloud`
- `~/.config/gh`
- `~/.claude`
- `~/.codex`

Project-level:

- uncommitted files from `git status --short`
- `.env`, `.env.local`, `.env.*`
- migration or schema files not yet committed
- local project config used in development

## Runtime state checklist

In addition to files, inspect what the source machine is actively running. Do not migrate runtime processes directly, but record them and decide how they should be recreated.

Classify runtime items into:

- **Destination-provided**: services the destination template/host should already manage
- **User-managed daemons**: PM2 apps, supervisord programs, custom agent wrappers, long-running CLIs
- **Project dev services**: `next dev`, `uvicorn`, `npm run dev`, `docker compose up`
- **Stateful local dependencies**: PostgreSQL, Redis, local volumes, SQLite DBs

Useful commands:

```bash
systemctl list-units --type=service --state=running
ps -eo pid,ppid,lstart,cmd
pm2 list
ss -lntp
docker ps
find ~/code -maxdepth 4 -type f \( -name 'docker-compose.yml' -o -name 'compose.yml' \)
```

Record for each runtime item:

- what is listening
- which project owns it
- whether it should exist automatically on the destination
- whether only config/data should be migrated
- what restore command should be run later

For SSH state, record separately:

- which private key(s) are expected to work
- whether the destination already has required `authorized_keys` entries
- whether `authorized_keys` should be merged instead of replaced

## Heuristics and lessons learned

- Prefer reproducible manifests over ad-hoc migration decisions
- Do not migrate `vendor/` trees wholesale by default even when modified; identify the actual edited files or subtrees first
- Do not assume one process manager; inspect PM2, supervisord, systemd user services, and similar supervisor state before deciding what needs restoration
- Docker port listeners may remain even when `docker ps` is empty or stale state exists; confirm both container state and compose files before planning restoration
- If a local app exposes a TCP port but is clearly a dev server (`next dev`, `uvicorn --reload`), restore it via source + env + start command, not by migrating process state
- Treat local SQLite DBs and app auth DBs as data, not cache, when they back user tools or dashboards
- Tool-specific dashboards or local helper UIs can be excluded unless the user explicitly wants their app state restored
- Large multi-vendor repos can be excluded wholesale when they are not part of the current migration target
- Service inventory should still be recorded even when the user chooses not to restore services immediately on the destination
- Test the exact transfer primitive you plan to use (`ssh`, `scp`, `rsync`) before committing to that path
- Migrated dotfiles can reintroduce legacy shell hooks that the destination template already removed; after sync, re-run a targeted cleanup/verification for deprecated tool references

## Deliverables for each migration task

Produce:

1. A must-migrate list
2. An optional list
3. A skip list
4. A service inventory with restore classification
5. Exact copy commands
6. Dry-run commands
7. Post-copy verification commands
8. Optional restore commands for services the user wants brought back
9. A final migration summary

The final migration summary should include:

- migrated files/directories summary
- intentionally skipped items
- services recorded for later restoration
- verification results
- transfer path used (for example direct SSH vs alias/proxy)
- useful performance data when measured, such as elapsed time, approximate throughput, or file-size benchmarks
- any cleanup or follow-up still recommended

For risky migrations, present the manifest and commands before running copy commands.
