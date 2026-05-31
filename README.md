# AgentOS

> A governance framework for multi-agent AI development. Provides branching strategy, commit standards, and structured handoff protocols for Claude Code, Antigravity, and other AI coding agents.

## What This Is

AgentOS is a **template repository** that establishes a shared "operating system" of rules that AI agents follow when collaborating on a codebase. It solves the coordination problem:

- **Branching protection** — Agents never touch `main` directly
- **Sync-before-start** — Agents always pull latest before coding
- **Structured handoffs** — A parsable `TODO_AGENT.md` template prevents context loss between sessions
- **Agent-specific proxies** — Each agent reads its own config file that routes to the master `AGENTS.md`

## Quick Start

### New Project (from template)

```bash
new-ai-project my-app
```

### Retrofit an Existing Project

```bash
cd ~/Work/Tech/my-existing-project
apply-agent-os
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
└── README.md              # You are here
```

## Shell Functions

Add these to your `~/.zshrc` to automate project bootstrapping:

```bash
# Create a new project from the AgentOS template
function new-ai-project() {
  if [ -z "$1" ]; then
    echo "Error: Provide a project name (e.g., new-ai-project my-app)"
    return 1
  fi

  echo "🚀 Bootstrapping AgentOS for $1..."
  gh repo create "$1" --template="Oudoo/AgentOS" --private --clone
  cd "$1" || exit
  echo "## Current Status\n- Fresh AgentOS initialization." > TODO_AGENT.md
  echo "✅ AgentOS deployed. Repository $1 is ready for Claude and Antigravity."
}

# Inject AgentOS governance into an existing repo (works with private repos)
function apply-agent-os() {
  # Guard: must be inside a git repo
  if ! git rev-parse --is-inside-work-tree &>/dev/null; then
    echo "❌ Error: Not inside a git repository."
    return 1
  fi

  local TEMPLATE_REPO="Oudoo/AgentOS"
  local FILES=("AGENTS.md" "CLAUDE.md" "TODO_AGENT.md" ".agent/rules/sync.md")

  echo "🔄 Injecting AgentOS governance from $TEMPLATE_REPO..."

  # Download each file using gh api (authenticates for private repos)
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

  # Preview changes before committing
  echo ""
  git add AGENTS.md CLAUDE.md .agent/ TODO_AGENT.md
  git --no-pager diff --cached --stat

  echo ""
  read -q "REPLY?Commit these changes? (y/n) "
  echo ""

  if [[ "$REPLY" =~ ^[Yy]$ ]]; then
    git commit -m "chore: implement AgentOS governance framework"
    echo "✅ AgentOS applied to existing project."
  else
    git reset HEAD AGENTS.md CLAUDE.md .agent/ TODO_AGENT.md &>/dev/null
    echo "⏪ Aborted. Changes unstaged — files are still on disk but not committed."
  fi
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

## License

MIT
