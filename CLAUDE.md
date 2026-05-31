# Claude Code System Prompt Proxy

You are bound by the global AgentOS governance model. 

Before processing any requests or analyzing the directory, you MUST first read the master ruleset located at `.agent/AGENTS.md`.

Obey the branching, isolation, and commit protocols strictly.

1. Read `.agent/AGENTS.md` for global rules — it is the single source of truth.
2. Run `git fetch origin && git pull --rebase origin $(git branch --show-current)` before starting any task.
3. Work strictly on feature branches. NEVER commit to `main`.
4. Stage, commit, and push before waiting for instructions or concluding a session.
5. Before concluding, update `.agent/HANDOFF.md` using the handoff template defined in `.agent/AGENTS.md`.