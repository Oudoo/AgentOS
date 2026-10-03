# Shared working agreement

## Start and ownership
1. Read root AGENTS.md, this agreement, HANDOFF.md, and the relevant runbook.
2. Run `python3 scripts/agentos.py doctor` and `status`. The coordination repository's
   `agentos-state` branch holds current tasks, handoffs, and infrastructure locks.
3. Work only on the human owner's assignment. Claim it with your actor and unique
   session name before editing. A model name is a label, not an identity.
4. Inspect Git status, fetch origin, and compare your branch with its remote. Never
   automatically rebase dirty/divergent work, discard changes, switch another
   session's branch, or rewrite published history.
5. Create a semantic feature branch. Use separate worktrees when sessions overlap;
   follow the host's managed-worktree instructions. No code on main.

## Work and handoff
- Keep edits within the assigned scope. Prefer relevant files and the repo map.
- Inspect the diff and commit explicit paths; never automatically `git add .`.
- Push the intended branch explicitly and open a PR. Test the changed behavior.
- `checkpoint` records state, blockers, evidence, and the precise next step without
  committing working files or executing your text.
- `handoff --to claude|codex|gemini|human` requires clean, pushed code. The next
  assistant reads the ledger and claims the task. Separate tasks prevent assistants
  overwriting a shared handoff. HANDOFF.md points to the live ledger.
- Release infrastructure locks before handoff. Locks never silently expire; ask the
  owner to resolve an abandoned lock after checking the old session stopped.
- Cleanup/review/audit commits carry no AI byline. Feature commits use standard
  attribution. Answer truthfully if asked about assistance.

## Production and secrets
- GitHub records changes; Coolify executes owner-approved deployments.
- Acquire the shared environment lock before infrastructure changes. One writer
  per environment. A Git lock coordinates work; it does not enforce RBAC.
- Require a reviewed SHA, backup/restore evidence, health checks, and rollback
  before production cutover. Record actor, Git identity, SHA, result, and evidence.
- Agents get sanitized status and narrowly scoped app actions. No root SSH, Docker
  group, broad sudo, owner dashboard automation, or admin API tokens.
- Keep passwords, keys, OTPs, recovery codes, .env values, dumps, and customer data
  out of Git, handoffs, task records, terminal output, and chat. Use secret references.
- Instruction files do not enforce access. Provision separate scoped identities;
  shared credentials cannot distinguish assistants. Verify actual branch rules and
  server-side deployment restrictions.
- These files authorize no assistant messages, API spending, or deployment.
