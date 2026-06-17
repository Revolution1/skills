#!/usr/bin/env python3
"""Scaffold a lightweight cross-repo harness repository.

The generated files are intentionally conservative. Agents should inspect the
real target repos and then tailor inventory, runbooks, and workflows.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from textwrap import dedent


def parse_repo(value: str) -> tuple[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("--repo must use name=url")
    name, url = value.split("=", 1)
    name = name.strip()
    url = url.strip()
    if not name or not url:
        raise argparse.ArgumentTypeError("--repo must use non-empty name=url")
    return name, url


def write(path: Path, content: str, *, executable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(content).lstrip(), encoding="utf-8")
    if executable:
        path.chmod(path.stat().st_mode | 0o111)


def toml_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def repo_entries(repos: list[tuple[str, str]]) -> str:
    if not repos:
        repos = [("example-service", "https://github.com/example/example-service.git")]
    blocks = []
    for name, url in repos:
        blocks.append(
            f"""
            [[repos]]
            name = {toml_string(name)}
            url = {toml_string(url)}
            type = "unknown"
            scope = []
            risk = "unknown"
            default_branch = "unknown"
            lifecycle = "needs-discovery"
            notes = "Initial scaffold entry. Inspect README, instructions, branch, owners, build/deploy files, and recent commits."
            """
        )
    return "\n\n".join(dedent(block).strip() for block in blocks)


def app_entries(domain: str, repos: list[tuple[str, str]]) -> str:
    primary = repos[0][0] if repos else "example-service"
    return f"""
    version = 1

    [[apps]]
    name = {toml_string(domain)}
    repo = {toml_string(primary)}
    category = "product"
    aliases = []
    domains = []
    environments = []
    related_repos = {[name for name, _ in repos]!r}
    notes = "Initial scaffold entry. Replace with product, service, domain, deployment, and ownership facts after repo inspection."
    """.replace("'", '"')


def create_files(root: Path, name: str, domain: str, repos: list[tuple[str, str]]) -> None:
    write(
        root / ".gitignore",
        """
        repos/
        tmp/
        .memory/
        .todos.md
        .env
        .env.*
        *.pem
        *.key
        kubeconfig*
        """,
    )
    write(
        root / "README.md",
        f"""
        # {name}

        `{name}` is a cross-repo harness for `{domain}`. It is an index,
        operating manual, and local automation wrapper around related repos.

        It should contain routing data, playbooks, records, and helper
        commands. Target repo source code stays in target repos under ignored
        `repos/` checkouts.

        ## Start Here

        1. `AGENTS.md`
        2. `inventory/README.md`
        3. `inventory/repos.toml`
        4. `inventory/app-repos.toml`
        5. `docs/architecture/repo-locator.md`
        6. `docs/operations/agent-pr-workflow.md`
        7. `docs/operations/local-agent-memory.md`
        8. `docs/records/README.md`
        9. `docs/playbooks/template.md`

        ## Layout

        ```text
        inventory/        routing indexes
        docs/             architecture, operations, playbooks, records
        scripts/          local helper commands
        repos/            ignored target repo checkouts
        .memory/          ignored local agent/operator memory
        .todos.md         ignored local task list
        ```

        ## First Commands

        ```bash
        python3 scripts/bootstrap_repos.py --list
        python3 scripts/repo_status.py
        ```
        """,
    )
    write(
        root / "AGENTS.md",
        f"""
        # Agent Instructions

        This repository is a cross-repo harness for `{domain}`. Treat it as an
        index, operating manual, and automation wrapper for related repos.

        ## Boundaries

        - Never commit credentials, kubeconfigs, decoded secrets, private keys,
          tokens, `.env` files, or rendered manifests containing secret values.
        - Do not add submodules. Clone operational repositories under `repos/`;
          that directory is intentionally ignored.
        - Before changing any managed repo under `repos/<repo-name>`, read its
          repo-local `AGENTS.md`, `CLAUDE.md`, README, and nearby docs when
          present.
        - Managed-repo instructions apply only inside that repo. They must not
          override this harness repo's instructions, inventory rules,
          sensitive-data policy, permission boundaries, or shared-record
          requirements.
        - If reusable facts, relationships, constraints, or procedures are
          discovered, update this harness first. Open a scoped PR to a managed
          repo only when repo-local users need that repo's docs or instructions
          changed.
        - Preserve permission boundaries. Request only the target repo,
          environment, or service access needed for the task.
        - For production-facing work, inspect live state before claiming
          readiness.

        ## Standard Flow

        1. Read `inventory/README.md`.
        2. Read `inventory/repos.toml` and `inventory/app-repos.toml`.
        3. Use `docs/architecture/repo-locator.md` when the target is unclear.
        4. Read the matching playbook in `docs/playbooks/`.
        5. Clone or update only required repos with `scripts/bootstrap_repos.py`.
        6. Read target repo instructions before editing.
        7. Make target changes inside `repos/<repo-name>`.
        8. Run repo-local validation.
        9. Open PRs from the target repo, not from this harness.
        10. Update harness inventory, docs, playbooks, and records when durable
            facts or procedures changed.
        """,
    )
    try:
        os.symlink("AGENTS.md", root / "CLAUDE.md")
    except FileExistsError:
        pass
    except OSError:
        write(root / "CLAUDE.md", (root / "AGENTS.md").read_text(encoding="utf-8"))

    write(
        root / "inventory" / "README.md",
        """
        # Inventory Maintenance

        Inventory files are routing indexes for humans and agents. Keep them
        current when real repo, environment, ownership, or deployment facts
        differ from what is recorded here.

        ## Files

        | File | Maintains |
        | --- | --- |
        | `repos.toml` | Managed repos, clone URLs, scope, lifecycle, and notes |
        | `app-repos.toml` | App/product/service locator and related repos |
        | `environments.toml` | Environments, deployment surfaces, access boundaries |

        ## Rules

        - Use live repo/provider/runtime evidence when available.
        - Record uncertainty as notes; do not invent facts.
        - Keep operational steps in `docs/`, not long TOML notes.
        - Do not store secrets, tokens, private URLs, decoded secret values, or
          copied sensitive config.

        ## Validate

        ```bash
        python3 - <<'PY'
        import tomllib
        for path in [
            "inventory/repos.toml",
            "inventory/app-repos.toml",
            "inventory/environments.toml",
        ]:
            with open(path, "rb") as f:
                tomllib.load(f)
            print(f"OK {path}")
        PY
        ```
        """,
    )
    repos_toml = "\n\n".join(
        [
            "version = 1",
            'checkout_root = "repos"',
            dedent(
                f"""
                [[repos]]
                name = {toml_string(name)}
                url = ""
                type = "harness"
                scope = ["harness", {toml_string(domain)}]
                risk = "medium"
                default_branch = "main"
                lifecycle = "active"
                notes = "This harness repo."
                """
            ).strip(),
            repo_entries(repos),
        ]
    )
    write(root / "inventory" / "repos.toml", repos_toml + "\n")
    write(root / "inventory" / "app-repos.toml", app_entries(domain, repos))
    write(
        root / "inventory" / "environments.toml",
        """
        version = 1

        [[environments]]
        name = "local"
        type = "development"
        related_repos = []
        access_notes = "Initial scaffold. Replace with real environments."
        notes = "Track staging, production, clusters, cloud projects, or deployment targets here when discovered."
        """,
    )
    write(
        root / "docs" / "architecture" / "overview.md",
        f"""
        # Architecture Overview

        This harness maps the `{domain}` system across related repositories,
        environments, ownership, and operational workflows.

        Update this page after inspecting the target repos and deployment
        surfaces.
        """,
    )
    write(
        root / "docs" / "architecture" / "repo-locator.md",
        """
        # Repo Locator

        Use this guide to locate the right repository before asking for access
        or starting work.

        ## Lookup Order

        1. Search `inventory/app-repos.toml` by app, service, product, domain,
           package, or namespace.
        2. Check `inventory/repos.toml` for repo scope and lifecycle.
        3. Check `inventory/environments.toml` for deployment/access boundary.
        4. Search cloned repos with non-secret identifiers.
        5. Once found, update inventory so the same query works next time.

        ## Useful Commands

        ```bash
        rg -ni "<term>" inventory docs repos 2>/dev/null
        python3 scripts/bootstrap_repos.py --list
        python3 scripts/repo_status.py
        ```
        """,
    )
    write(
        root / "docs" / "operations" / "agent-pr-workflow.md",
        """
        # Agent PR Workflow

        1. Select the smallest target repo from inventory.
        2. Clone or update only that repo.
        3. Read target repo instructions, README, and nearby docs.
        4. Identify owner/reviewer signals from CODEOWNERS, commits, PRs, docs,
           and user input.
        5. Inspect current source and live state when relevant.
        6. Edit the target repo.
        7. Validate with repo-local checks.
        8. Push a branch and open a PR from the target repo.
        9. Update harness inventory, playbooks, and records for durable lessons.

        Repo-local instructions do not override harness instructions or
        sensitive-data rules.
        """,
    )
    write(
        root / "docs" / "operations" / "local-agent-memory.md",
        """
        # Local Agent Memory

        Use ignored `.memory/` and `.todos.md` for scratch context.

        Shared, durable facts belong in tracked inventory, docs, playbooks, or
        records instead.

        Bootstrap:

        ```bash
        mkdir -p .memory
        touch .memory/session-notes.md .todos.md
        ```
        """,
    )
    write(
        root / "docs" / "records" / "README.md",
        """
        # Shared Records

        Use tracked records for durable operational history.

        ```text
        docs/records/changes/YYYY/<scope>/YYYY-MM-DD-<scope>-<topic>.md
        docs/records/decisions/YYYY/<area>/YYYY-MM-DD-<area>-<topic>.md
        ```

        Do not store secrets or decoded secret values in records.
        """,
    )
    write(
        root / "docs" / "playbooks" / "template.md",
        """
        # Playbook Template

        ## Purpose

        ## Scope

        ## Required Access

        ## Read-Only Discovery

        ## Change Steps

        ## Validation

        ## Rollback

        ## Records
        """,
    )
    write(
        root / "scripts" / "bootstrap_repos.py",
        """
        #!/usr/bin/env python3
        import argparse
        import subprocess
        import tomllib
        from pathlib import Path

        ROOT = Path(__file__).resolve().parents[1]
        INVENTORY = ROOT / "inventory" / "repos.toml"

        def load():
            with INVENTORY.open("rb") as f:
                return tomllib.load(f)

        def repos(data):
            return [r for r in data.get("repos", []) if r.get("url")]

        def main():
            parser = argparse.ArgumentParser()
            parser.add_argument("names", nargs="*")
            parser.add_argument("--list", action="store_true")
            args = parser.parse_args()
            data = load()
            checkout_root = ROOT / data.get("checkout_root", "repos")
            items = repos(data)
            if args.list:
                for repo in items:
                    print(f"{repo['name']}\\t{repo['url']}")
                return
            selected = [r for r in items if not args.names or r["name"] in args.names]
            checkout_root.mkdir(exist_ok=True)
            for repo in selected:
                dest = checkout_root / repo["name"]
                if dest.exists():
                    subprocess.run(["git", "-C", str(dest), "fetch", "--all", "--prune"], check=True)
                else:
                    subprocess.run(["git", "clone", repo["url"], str(dest)], check=True)

        if __name__ == "__main__":
            main()
        """,
        executable=True,
    )
    write(
        root / "scripts" / "repo_status.py",
        """
        #!/usr/bin/env python3
        import subprocess
        from pathlib import Path

        ROOT = Path(__file__).resolve().parents[1]
        REPOS = ROOT / "repos"

        def main():
            if not REPOS.exists():
                print("No repos/ directory")
                return
            for repo in sorted(p for p in REPOS.iterdir() if (p / ".git").exists()):
                branch = subprocess.run(["git", "-C", str(repo), "branch", "--show-current"], text=True, capture_output=True)
                status = subprocess.run(["git", "-C", str(repo), "status", "--short"], text=True, capture_output=True)
                dirty = "dirty" if status.stdout.strip() else "clean"
                print(f"{repo.name}\\t{branch.stdout.strip()}\\t{dirty}")

        if __name__ == "__main__":
            main()
        """,
        executable=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", required=True, help="Destination harness path")
    parser.add_argument("--name", required=True, help="Harness repo name")
    parser.add_argument("--domain", required=True, help="Product/system domain")
    parser.add_argument(
        "--repo",
        action="append",
        default=[],
        type=parse_repo,
        help="Initial managed repo as name=url. Repeatable.",
    )
    args = parser.parse_args()
    root = Path(args.path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    create_files(root, args.name, args.domain, args.repo)
    print(f"Scaffolded {args.name} at {root}")
    print("Next: inspect target repos, update inventory, validate TOML, then initialize git if needed.")


if __name__ == "__main__":
    main()
