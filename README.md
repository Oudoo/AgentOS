# AgentOS

> A governance framework for multi-agent AI development. Provides branching strategy, worktree isolation, commit standards, and structured handoff protocols for Claude Code, Antigravity, and other AI coding agents.

## What This Is

AgentOS is a **template repository** that establishes a shared "operating system" of rules that AI agents follow when collaborating on a codebase. It solves the coordination problem:

- **Branching protection** — Agents never touch `main` directly
- **Clean branch names** — No random strings, IDs, or hashes appended
- **Worktree isolation** — Multiple agents code simultaneously in separate directories
- **Sync-before-start** — Agents always pull latest before coding
- **Structured handoffs** — A parsable `TODO_AGENT.md` template prevents context loss between sessions
- **Agent-specific proxies** — Each agent reads its own config file that routes to the master `AGENTS.md`

## Quick Start

### New Project (from template)

```bash
new my-app
```

### Retrofit an Existing Project

```bash
cd ~/Work/Tech/my-existing-project
agent-os
```

### Create an Isolated Worktree for an Agent

```bash
worktree feat/add-login
cd .worktrees/feat/add-login
# Start Claude Code or Antigravity inside this folder
```

### Manual Setup

1. Use this template on GitHub → "Use this template" → "Create a new repository"
2. Clone your new repo locally
3. Start coding with any AI agent — they'll read the governance files automatically

## File Structure

```
├── AGENTS.md              # Master governance (source of truth)
├── CLAUDE.md              # Claude Code proxy → reads AGENTS.md
├── .agent/rules/sync.md   # Antigravity proxy → reads AGENTS.md
├── TODO_AGENT.md          # Handoff state template
├── .gitignore             # Excludes .worktrees/
└── README.md              # You are here
```

## Shell Functions

Add these to your `~/.zshrc` to automate project bootstrapping:

```bash
# Usage: new <project-name>
# Creates a new private repo from the AgentOS template
function new() {
  if [ -z "$1" ]; then
    echo "Usage: new <project-name>"
    return 1
  fi

  echo "🚀 Bootstrapping AgentOS for $1..."
  gh repo create "$1" --template="Oudoo/AgentOS" --private --clone
  cd "$1" || exit
  echo "## Current Status\n- Fresh AgentOS initialization." > TODO_AGENT.md
  echo "✅ AgentOS deployed. Repository $1 is ready."
}

# Usage: agent-os
# Injects AgentOS governance into the current repo (works with private repos)
function agent-os() {
  if ! git rev-parse --is-inside-work-tree &>/dev/null; then
    echo "❌ Not inside a git repository."
    return 1
  fi

  local TEMPLATE_REPO="Oudoo/AgentOS"
  local FILES=("AGENTS.md" "CLAUDE.md" "TODO_AGENT.md" ".agent/rules/sync.md" ".gitignore")

  echo "🔄 Injecting AgentOS governance from $TEMPLATE_REPO..."

  for file in "${FILES[@]}"; do
    local dir=$(dirname "$file")
    [ "$dir" != "." ] && mkdir -p "$dir"

    local content
    content=$(gh api "repos/$TEMPLATE_REPO/contents/$file" --jq '.content' 2>/dev/null | base64 --decode 2>/dev/null)

    if [ -z "$content" ]; then
      echo "❌ Failed to fetch $file — aborting. No files were changed."
      return 1
    fi

    echo "$content" > "$file"
    echo "  ✓ $file"
  done

  echo ""
  git add AGENTS.md CLAUDE.md .agent/ TODO_AGENT.md .gitignore
  git --no-pager diff --cached --stat

  echo ""
  read -q "REPLY?Commit these changes? (y/n) "
  echo ""

  if [[ "$REPLY" =~ ^[Yy]$ ]]; then
    git commit -m "chore: implement AgentOS governance framework"
    echo "✅ AgentOS applied."
  else
    git reset HEAD AGENTS.md CLAUDE.md .agent/ TODO_AGENT.md .gitignore &>/dev/null
    echo "⏪ Aborted. Files on disk but not committed."
  fi
}

# Usage: worktree <branch-name>
# Creates an isolated worktree for multi-agent concurrency
function worktree() {
  if [ -z "$1" ]; then
    echo "Usage: worktree <branch-name>"
    return 1
  fi

  mkdir -p .worktrees
  git worktree add ".worktrees/$1" -b "$1"
  echo "✅ Worktree ready at .worktrees/$1"
  echo "   cd .worktrees/$1 to start coding"
}
```

Then run `source ~/.zshrc` to activate.

## How It Works

1. **Agent starts a session** → reads its proxy file (`CLAUDE.md` or `.agent/rules/sync.md`)
2. **Proxy routes to `AGENTS.md`** → agent learns the governance rules
3. **Agent creates a feature branch** → never touches `main`
4. **Agent codes, commits, pushes** → preserves state on remote
5. **Agent concludes** → fills `TODO_AGENT.md` with structured handoff state
6. **Next agent reads `TODO_AGENT.md`** → resumes instantly without re-analyzing the entire codebase

## Worktree Isolation (Multi-Agent Concurrency)

By default, Git swaps files inside a single folder. With `git worktree`, you create a **separate physical folder** for each branch. This lets multiple agents code simultaneously without collisions.

### Setup

```bash
# One-time: .gitignore already excludes .worktrees/ via this template
mkdir -p .worktrees
```

### Create a worktree

```bash
worktree feat/add-login
# Or manually:
git worktree add .worktrees/feat/add-login -b feat/add-login
```

### Use with agents

1. `cd .worktrees/feat/add-login`
2. Start Claude Code or Antigravity **inside that folder**
3. The agent codes in complete filesystem isolation
4. Commits inside the worktree are instantly recognized by the main repo

### Clean up after merge

```bash
git worktree remove .worktrees/feat/add-login
```

### Why Worktrees?

- **Antigravity codes in Folder A** while **Claude debugs in Folder B** — zero file conflicts
- Both share the same `.git` history in the background
- No need to push to GitHub to sync locally between worktrees
- Each agent can run its own dev server on a different port

> 📺 [Codex multi-agent worktree demo](https://www.youtube.com/watch?v=fVdBEgVE0wI) — visual walkthrough of worktree isolation for AI agents.

## License

MIT
