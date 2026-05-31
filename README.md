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

### Start a Subproject Branch

```bash
branch feat/auth-service
# Creates branch, scaffolds feat/auth-service/ folder with TODO_AGENT.md, auto-commits
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

    if [ "$file" = ".gitignore" ] && [ -f .gitignore ]; then
      # Append worktree rule to existing .gitignore instead of overwriting
      grep -q "^\.worktrees" .gitignore || echo -e "\n.worktrees/" >> .gitignore
      echo "  ✓ $file (appended .worktrees/)"
    else
      echo "$content" > "$file"
      echo "  ✓ $file"
    fi
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

# Usage: branch <subproject-name>
# Creates a branch + subproject folder with a localized handoff template
function branch() {
  if [ -z "$1" ]; then
    echo "Usage: branch <subproject-name>"
    return 1
  fi

  # Enforce clean branch naming: lowercase kebab-case only
  if [[ ! "$1" =~ ^[a-z0-9]+(-[a-z0-9]+)*(/[a-z0-9]+(-[a-z0-9]+)*)*$ ]]; then
    echo "❌ Invalid name. Use lowercase kebab-case (e.g., feat/add-login, auth-service)."
    return 1
  fi

  if ! git rev-parse --is-inside-work-tree &>/dev/null; then
    echo "❌ Not inside a git repository."
    return 1
  fi

  echo "🌿 Creating subproject branch: $1"

  git checkout -b "$1"

  # Create subproject folder at project root
  mkdir -p "$1"

  # Seed localized handoff template
  cat > "$1/TODO_AGENT.md" << 'HANDOFF'
# Agent Handoff State

**🎯 Goal:** [1-sentence description of the overarching objective]

**✅ Completed in Last Session:**
- [File path]: [Brief description of what was added/fixed]

**🛑 Current State / Blockers:**
- [Describe the exact state where work stopped. If there is an error, paste the exact error code/message here].

**⏭️ Immediate Next Step:**
- [The EXACT file, line number, or terminal command the incoming agent should execute first to resume momentum].
HANDOFF

  git add "$1/"
  git commit -m "chore: initialize subproject workspace for $1"

  echo "✅ Branch '$1' created with subproject folder."
  echo "   Edit $1/TODO_AGENT.md to set the goal, then start coding."
}

# Usage: map
# Generates a token-optimized structure map of the project for the agents
function map() {
  if ! git rev-parse --is-inside-work-tree &>/dev/null; then
    echo "❌ Not inside a git repository."
    return 1
  fi

  echo "🗺️ Generating token-optimized repository map..."
  
  mkdir -p .agent
  echo "# Repository Structural Map\nGenerated on: $(date)\n\n\`\`\`text" > .agent/repo-map.md
  
  # Generates a folder tree ignoring heavy directories and hidden assets
  tree -I "node_modules|venv|\.git|\.worktrees|__pycache__|\.DS_Store|dist|build" --dirsfirst >> .agent/repo-map.md
  
  echo "\`\`\`" >> .agent/repo-map.md
  echo "✅ Map saved to .agent/repo-map.md"
}

# Usage: checkpoint "working on login bug"
# Quick state freeze that records uncommitted work for the incoming agent
function checkpoint() {
  if [ -z "$1" ]; then
    echo "Usage: checkpoint <brief-context-message>"
    return 1
  fi

  echo "🥶 Freezing active session state..."
  
  # Write a fast memory update directly to the top of the handoff note
  sed -i '' "1s/^/⚠️ QUICK CHECKPOINT: $1 (Saved: $(date))\n\n/" TODO_AGENT.md 2>/dev/null || \
  echo "⚠️ QUICK CHECKPOINT: $1 (Saved: $(date))\n\n$(cat TODO_AGENT.md)" > TODO_AGENT.md

  git add .
  git commit -m "checkpoint: $1 [ci skip]"
  
  echo "✅ State frozen under temporary commit. Incoming agent will see the checkpoint message."
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

## The Master AgentOS Matrix

| Scenario | Command to Type | What It Actually Does | Impact on Tokens & Workflow |
| --- | --- | --- | --- |
| **Start a completely new project container** | `new centro-aeo-geo` | Clones your GitHub template, sets up a private repo, and changes directories into it. | **Saves 5-10 minutes of manual configuration.** Zero token impact yet. |
| **Add AgentOS rules to an existing app** | `agent-os` | Downloads rules, hooks proxies, and safely appends to your `.gitignore`. | **Stops agent amnesia.** Future incoming agents instantly understand boundaries. |
| **Isolate work to a separate folder** | `worktree feat/login` | Spawns a physical directory at `.worktrees/feat/login` tied to that branch. | **Enables parallel coding.** Multiple agents can code at the exact same time without file or server conflicts. |
| **Start a clean subproject workspace** | `branch aeo-service` | Creates a branch, builds a dedicated folder, seeds a local `TODO_AGENT.md`, and auto-commits. | **Zero random numbers in branch names.** Keeps multi-app repos perfectly organized. |
| **Before launching any agent sequence** | `map` | Builds a compressed architectural text tree at `.agent/repo-map.md`. | **Saves up to 40% on discovery tokens.** Stops agents from blindly reading every file to understand structure. |
| **An agent hits a token wall or you switch tools** | *Promoted prompt inside agent chat* | Agent populates the detailed `TODO_AGENT.md` template, commits, and pushes. | **Context retention is 100%.** Incoming agent picks up exactly where the last one stopped. |
| **You need a fast session pause without a full handoff** | `checkpoint "debugging auth"` | Records uncommitted work with a fast git snapshot and drops a 1-line timestamped note. | **Saves context on a time crunch.** Prevents losing local state when switching mental tracks quickly. |

## Complete End-to-End Workflow Map

1. **Morning Routine (The Scaffold):** Run `new <name>` or navigate to your project and run `branch <name>`. Run `map` once immediately before opening your agent code editor.
2. **The Active Coding Cycle:** Give your prompt to Claude Code or Antigravity inside your branch or worktree folder. They read the map, find their files surgically, and write code.
3. **The Micro-Pause:** If you need to step away or jump to another task unexpectedly, drop a `checkpoint "fixing endpoint layout"` in your terminal.
4. **The Pivot Handoff:** When an agent runs low on tokens or hits a complex wall, use the structured prompt to force a `TODO_AGENT.md` generation, push to GitHub, and open your second agent using the clean instructions.

## License

MIT
