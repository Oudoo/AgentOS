# Claude Code Protocol

1. Read `AGENTS.md` for global rules — it is the single source of truth.
2. Run `git fetch origin && git pull --rebase origin $(git branch --show-current)` before starting any task.
3. Work strictly on feature branches. NEVER commit to `main`.
4. Stage, commit, and push before waiting for instructions or concluding a session.
5. Before concluding, update `TODO_AGENT.md` using the handoff template defined in `AGENTS.md`.