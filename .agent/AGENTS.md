# AgentOS Global Governance Framework

This repository is actively developed by multiple AI agents (Claude Code, Antigravity 2.0) alongside human developers.

## 1. Core Directives
- **Source of Truth:** GitHub is the central synchronization point. Never assume local files are up to date.
- **Initialization:** ALWAYS run `git fetch origin` and `git pull --rebase origin $(git branch --show-current)` before analyzing the codebase for a new prompt.

## 2. Branching Strategy
- NEVER commit directly to the `main` branch.
- **Pre-Task Sequence:** Before beginning any new coding task, analyze the user's prompt, generate a semantic branch name (e.g., `feat/your-feature`), and execute `git checkout -b <branch_name>`.

### Branching & Workspace Isolation
You are strictly forbidden from writing code on the `main` branch.

**Pre-Execution Branching Sequence:**
1. When receiving a new task prompt, analyze the intent (feature, fix, refactor, chore).
2. Generate a semantic branch name (e.g., `feat/zoho-api-sync`, `fix/odoo-timeout`).
3. Execute `git fetch origin`.
4. Execute `git checkout -b <generated-branch-name>`.
5. Only AFTER confirming the branch creation may you begin file modifications or vibe coding sequences.

### Clean Branch Names
- Do **not** append random strings, IDs, ticket numbers, or hash codes to branch names.
- Use strictly human-readable semantic strings (e.g., `feat/add-login`, `fix/auth-timeout`, `refactor/api-layer`).
- Branch names must be lowercase, kebab-case, and prefixed with a type (`feat/`, `fix/`, `refactor/`, `chore/`).

### Worktree Isolation (Multi-Agent Concurrency)
When multiple agents need to work simultaneously on different features, use **Git Worktrees** for physical filesystem isolation instead of switching branches in a single directory.

**Worktree Rules:**
1. All worktrees live inside the `.worktrees/` directory at the project root.
2. To start a new isolated workspace: `git worktree add .worktrees/<Semantic-Name> -b <Semantic-Name>`.
3. Each agent operates exclusively inside its own worktree folder.
4. When the feature is merged, clean up with: `git worktree remove .worktrees/<Semantic-Name>`.
5. Never create worktrees outside the `.worktrees/` directory.

## 3. Commit Standards
- Commit frequently to your feature branch to preserve state.
- Use semantic commit messages (e.g., `feat: added zoho payload builder`, `fix: resolved auth token expiration`).
- Upon completing a logical milestone, execute `git push -u origin <branch_name>`.

## 4. Multi-Agent Handoff Protocol
When you hit a token limit, encounter a hard blocker, or are instructed to pause, you MUST perform a state handoff:
1. Stage and commit your current working state.
2. Overwrite `.agent/HANDOFF.md` strictly using the machine-readable template below. Be extremely concise.
3. Do not include conversational filler in your terminal output.

---

### Handoff Template to overwrite in `.agent/HANDOFF.md`:
```markdown
## LAST_AGENT
[Agent Name]

## BRANCH
[Branch Name]

## LAST_COMMIT
[Commit Hash]

## UPDATED
[Timestamp]

## GOAL
[1-sentence description of the overarching objective]

## CURRENT_STATE
[What works, what doesn't]

## BLOCKER
[Exact error message or logical roadblock]

## NEXT_STEP
[Exact file/line to edit next, or command to run]

## FILES
[List of active files the agent should load]
```

## 5. Token-Optimization Directives (CRITICAL)
To minimize token billing, you must strictly follow these structural execution rules:

1. **Orientation:** Before running widespread searches across the directory, open and read `.agent/repo-map.md` to learn the project structure instantly.
2. **Surgical Inspection:** Never read entire files exceeding 200 lines if you only need a specific block. Use targeted grep commands or line-specific views (e.g., viewing specific line ranges) to gather code context.
3. **No Redundant Queries:** Do not re-read files you modified in the same chat turn; rely on your internal session memory.