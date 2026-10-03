# AgentOS
Shared working memory for Mahmoud, Codex/ChatGPT, Claude, and Gemini through GitHub.
Small Markdown/JSON records and a standard-library Python CLI; no extra hosting,
model API bill, daemon, root access, or automatic deployment.

## What is shared
| File or branch | Purpose |
| --- | --- |
| AGENTS.md | Codex entry point and project rules |
| CLAUDE.md / GEMINI.md | Imports for Claude Code / Gemini CLI |
| .agent/AGENTS.md | One shared working agreement |
| .agent/config.json | Owner, project, actors, private coordinator URL |
| agentos-state branch | Per-task ownership, handoffs, evidence, environment locks |
| Private operations repo | Runbooks, infrastructure, environment/secret references, changes, health |
| App repository | Source, Dockerfile/Compose, tests, staging/production manifests |

Assistants claim an assigned task, work on isolated feature branches, and transfer
state explicitly. Git rejects competing stale ledger writes. A shared production
lock coordinates infrastructure changes across projects. The CLI never commits app
files, runs supplied commands, calls models, or deploys anything.

## Start
Requires Git and Python 3.9+ with normal Git authentication. No pip dependencies.
Use a private coordinator for real operations; this public repository is a template.

```sh
# Review the checkout first. Installation defaults to a dry run.
python3 scripts/agentos.py install /absolute/path/to/app
python3 scripts/agentos.py install /absolute/path/to/app --apply
# Configure the installed .agent/config.json owner/project/coordinator.
# On the private coordination repository, once:
python3 scripts/agentos.py init-state
# From any enrolled project:
python3 scripts/agentos.py doctor
python3 scripts/agentos.py status
```

Existing differing files stop installation before writing. Use
`--preserve-entrypoints` to retain existing root instructions, then manually add
the shared imports. Project-specific safety rules remain authoritative. Upgrade
through reviewed diffs; no global shell profile changes or destructive remote updater.

Read [daily workflow and access limits](docs/coordination.md) and the
[Mac → Coolify migration checklist](docs/migration.md). `--help` lists commands.

## Boundaries
GitHub identities and server-side permissions enforce access. Actor labels and
Markdown rules are coordination, not authentication or strict RBAC. Accounts shared
between assistants remain one security principal. Production deployment needs a
reviewed SHA, backup/restore evidence, a scoped interface, and owner approval.

Web chat projects need the relevant repository files or handoff supplied explicitly;
these instruction files configure coding clients and do not automatically synchronize
chats, install clients, or connect accounts. Never store secrets in this template or
the ledger. Recovery codes belong in the owner's password manager.

The previous README's shell snippets are retired: they overwrote governance files
and staged all working files. The [legacy visual guide](agentos_master_playbook.html)
is retained as a historical reference; use the current CLI and docs for commands.

## Verify
```sh
python3 -m unittest discover -s tests -v
```
Tests exercise real local Git repositories: competing writers, task/session
ownership, environment locks, handoffs, dirty/unpushed code refusal, safe text,
installer conflicts, symlinks, and duplicate initialization. No VPS/account access.
