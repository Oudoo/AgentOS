# Coordination without another service
Each code repository has assistant entry points and a Python CLI. Its config can
point to one private operations repository. That repository's `agentos-state`
branch is the live board: tasks, per-task handoffs, and environment locks.

Every ledger write clones the latest state into a temporary directory, checks
ownership/session conditions, commits only its changed records, and pushes a
normal fast-forward update. Git rejects competing stale pushes; the losing writer
must read the new state and retry. No force-push or automatic stale-action retry.
The same ledger coordinates all apps. Session names must be unique, even for the
same model. Locks never silently expire or get taken over.

This coordinates cooperating sessions; anyone with repository write permission
can edit records or spoof actor labels. Git records the credential's real identity.
Separate scoped accounts and server-side restrictions enforce least privilege.
It does not provide automatic chat synchronization or strict RBAC.

The CLI calls no models, SSH, Coolify, or deployment webhook. Text is data, never
shell commands. Web ChatGPT, Claude Projects, and Gemini chats must be explicitly
given the relevant GitHub files or an exported handoff. Filenames alone connect
neither web chats nor accounts.

## Daily flow
```sh
python3 scripts/agentos.py doctor
python3 scripts/agentos.py status
python3 scripts/agentos.py create abdo-containerize --title 'Prepare Abdo staging migration' --scope deploy --scope docs
# Create an isolated feature branch/worktree before claiming.
python3 scripts/agentos.py claim abdo-containerize --actor claude --session claude-abdo-prep
python3 scripts/agentos.py checkpoint abdo-containerize --actor claude --session claude-abdo-prep --state 'Dependencies inventoried' --next 'Add staging Compose' --evidence docs/inventory.md
# Review and commit explicit files; push the branch; then:
python3 scripts/agentos.py handoff abdo-containerize --actor claude --session claude-abdo-prep --to codex --state 'Staging ready' --next 'Review restore procedure' --evidence https://github.com/OWNER/APP/pull/1
```

Before an approved environment change use `lock production --task TASK --actor
ACTOR --session SESSION`, then `unlock production` with the same identity after
verification. The CLI has no deploy command. Use the actual app-scoped deployment
interface and owner approval. `review` transfers a clean/pushed task to human review;
`close --actor human --evidence URL` records completion. Actor checks are workflow
checks, not authentication. Abandoned locks require owner inspection and an explicit
reviewed change to the ledger; no automatic takeover.

`show TASK` prints the structured handoff. Checkpoint can record dirty work without
staging it; transfer/review refuses dirty or unpushed code.

## Bootstrap and adoption
Run `init-state` once on the private coordination repository. It creates a separate
orphan branch and refuses to replace an existing branch. It grants no server access.

From a reviewed AgentOS checkout, run `install /absolute/path/to/app` for a dry run,
then add `--apply`. All conflicts are checked before writing. Conflicts stop the
entire install. `--preserve-entrypoints` leaves existing AGENTS/CLAUDE/GEMINI files
untouched and reports the imports to add manually. No shell profile edits, downloaded
code execution, app commits, or uploads. Configure owner/project/coordination URL
after adoption. Upgrades use reviewed diffs, not destructive remote update scripts.

Official instruction loading:
- [Codex AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
- [Claude CLAUDE.md imports](https://code.claude.com/docs/en/memory)
- [Gemini GEMINI.md imports](https://geminicli.com/docs/cli/gemini-md/)

Verify imports in each coding client after adoption. These files install or sign
into no clients. Keep operational metadata private and secrets out of all records.
