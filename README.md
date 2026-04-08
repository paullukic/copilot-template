# Copilot Template

Reusable AI coding assistant configuration for any project. Works with **VS Code Copilot** and **Claude Code**. Includes agents, skills, prompts, a code-graph MCP server, and an OpenSpec-driven development workflow.

## Prerequisites

| Dependency | Required for | Install |
|-----------|-------------|---------|
| [OpenSpec CLI](https://github.com/openspec-dev/openspec) | Propose / Apply / Archive workflow | `npm i -g openspec` |
| Python 3.10+ | Code-graph MCP server (optional) | System package manager |
| [uv](https://docs.astral.sh/uv/) | Running code-graph without pip install (recommended) | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |

## Quick Start

### Option A: Automated (recommended)

Open this repo in your editor and run the initialize command. It asks for the target project path, detects the tech stack, copies files, and fills in all placeholders automatically.

| Tool | Command |
|------|---------|
| VS Code Copilot | `/opsx:initialize` or invoke the `initialize-project` skill |
| Claude Code | `/project:initialize` |

### Option B: Manual copy + guided setup

1. Copy files into your project:
   ```bash
   # Required
   cp -r .github/ /path/to/your-project/.github/
   cp AGENTS.md /path/to/your-project/

   # Claude Code support
   cp CLAUDE.md /path/to/your-project/
   cp -r .claude/ /path/to/your-project/.claude/

   # OpenSpec workflow
   cp -r openspec/ /path/to/your-project/openspec/
   ```

2. Open the target project and ask your AI tool to fill in the template:
   ```
   Read the copilot-instructions.md and fill in all _TBD_ and FILL placeholders
   based on this project's stack.
   ```

Both approaches read the project's `README.md`, `package.json`, `pom.xml`, etc. to detect the tech stack and fill in `_TBD_` / `<!-- FILL -->` placeholders.

## Which Tool for What

### Claude Code — full workflow in one conversation

Describe the task in one message. Claude Code reads `CLAUDE.md`, follows the full workflow (Plan → Propose → Apply → Quality Gates → Review Gate → Done) autonomously. Best for:
- New features, multi-file refactors, bug fixes
- Continuing work from a previous session (reads OpenSpec `tasks.md` automatically)

### VS Code Copilot — agents as single-purpose tools

Invoke agents directly for a specific job. Agent-to-agent handoffs require manual switching (by design — subagents don't receive their `.agent.md` tools). Best for:
- `@Reviewer` — code reviews while you're in the editor
- `@Explore` — fast codebase Q&A and search
- `@Debugger` — investigating errors in the terminal
- `@Planner` → `/opsx:propose` → `/opsx:apply` — full workflow (requires manual handoffs)

## Workflow

```
Plan ──► Propose ──► Implement ──► Quality Gates ──► Review Gate ──► Archive
 │         │            │              │                 │
 │    OpenSpec CLI   /opsx:apply    build/test      @Reviewer
 │    creates       works through   must pass       auto-invoked
 │    artifacts     tasks.md
 │
 @Planner (skip for clear-scope tasks)
```

| Step | VS Code Copilot | Claude Code |
|------|----------------|-------------|
| Plan | `@Planner` | `/project:plan` |
| Propose | `/opsx:propose add-dark-mode` | Automatic (part of workflow) |
| Explore | `/opsx:explore` | `/project:explore` |
| Implement | `/opsx:apply` | Automatic (part of workflow) |
| Review | Auto-invoked by apply skill | `/project:review` |
| Verify | `@Verifier` | `/project:verify` |
| Debug | `@Debugger` | `/project:debug` |
| Archive | `/opsx:archive` | Manual move to `archive/` |

## Structure

```
.github/
  copilot-instructions.md                    # Project conventions (single source of truth)
  agents/
    reviewer.agent.md                        # Strict code reviewer (read-only)
    debugger.agent.md                        # Root-cause analysis + minimal fixes
    planner.agent.md                         # Interview-driven planning (read-only)
    verifier.agent.md                        # Evidence-based completion checks (read-only)
    explore.agent.md                         # Fast codebase search and Q&A (read-only)
  skills/
    initialize-project/SKILL.md              # Interactive project setup (detects stack, fills template)
    openspec-apply-change/SKILL.md           # Implement tasks with verification gates
    openspec-propose/SKILL.md                # Propose a change with all artifacts
    openspec-explore/SKILL.md                # Explore mode — thinking partner
    openspec-archive-change/SKILL.md         # Archive completed changes
  prompts/
    opsx-initialize.prompt.md                # /opsx:initialize
    opsx-apply.prompt.md                     # /opsx:apply
    opsx-propose.prompt.md                   # /opsx:propose
    opsx-explore.prompt.md                   # /opsx:explore
    opsx-archive.prompt.md                   # /opsx:archive
  instructions/
    testing.instructions.md                  # Test conventions (auto-loaded for *.test.*)
    styling.instructions.md                  # CSS/style conventions (auto-loaded for *.css)
  code-graph/
    builder.py                               # Parses source files into SQLite graph
    server.py                                # MCP server exposing graph tools to agents
    visualize.py                             # HTML graph visualization
    requirements.txt                         # Only mcp>=1.0.0
    post-commit / post-merge / post-rewrite  # Git hooks for auto-updating the graph
.claude/
  commands/project/
    initialize.md                            # /project:initialize
    plan.md                                  # /project:plan
    explore.md                               # /project:explore
    debug.md                                 # /project:debug
    review.md                                # /project:review
    verify.md                                # /project:verify
  settings.local.json                        # Claude Code permissions
openspec/
  config.yaml                                # OpenSpec schema configuration
CLAUDE.md                                    # Claude Code entry point
AGENTS.md                                    # Cursor/Windsurf compatibility
user/
  brutal-honesty.instructions.md             # Global communication style (user-level)
```

## What's Included

### Convention Files

| File | Read by | Purpose |
|------|---------|---------|
| `.github/copilot-instructions.md` | VS Code Copilot | Single source of truth for project conventions |
| `CLAUDE.md` | Claude Code | Workflow + delegation + key conventions |
| `AGENTS.md` | Cursor, Windsurf | Thin pointer to copilot-instructions |
| `user/brutal-honesty.instructions.md` | VS Code (user-level) | Global communication style |

### Agents (VS Code + Claude Code)

There is no separate `@Implementer` agent. The agent that plans and proposes also implements directly.

| Agent | Purpose | Key features |
|-------|---------|-------------|
| **Reviewer** | Strict read-only code review | Manifest-driven (reads files, not diffs). Chain-of-verification. Evidence rule: fresh `read_file` quotes only. |
| **Debugger** | Root-cause analysis and minimal fixes | Reproduce → Evidence → Hypothesize → Fix → Verify. 3-failure circuit breaker. Post-fix scope check. |
| **Planner** | Interview-driven planning | Risk-based classification (auth/security always Complex). Measurable acceptance criteria. One question at a time. |
| **Verifier** | Independent completion checks | Self-challenges verdicts before issuing. Handles no-test-suite projects. |
| **Explore** | Fast read-only search and Q&A | Quick/medium/thorough depth levels. Structured output (Summary → Evidence → Details). |

### Skills (VS Code) / Commands (Claude Code)

| Skill | Command | Purpose |
|-------|---------|---------|
| `initialize-project` | `/project:initialize` | Interactive setup — detects stack, copies files, fills placeholders |
| `openspec-propose` | (automatic) | Create a change with all artifacts (proposal, specs, tasks) |
| `openspec-apply-change` | (automatic) | Implement tasks with verification gates and auto-review |
| `openspec-explore` | `/project:explore` | Thinking partner — explore ideas, investigate problems |
| `openspec-archive-change` | (manual) | Archive completed changes with optional delta spec sync |
| — | `/project:plan` | Interview-driven planning |
| — | `/project:debug` | Root-cause analysis and minimal fixes |
| — | `/project:review` | Strict code review |
| — | `/project:verify` | Evidence-based completion checks |

### Prompts (VS Code slash commands)

`/opsx:initialize`, `/opsx:apply`, `/opsx:propose`, `/opsx:explore`, `/opsx:archive` — thin wrappers that invoke the corresponding skills.

### Conditional Instructions

| File | Loaded when editing | Purpose |
|------|-------------------|---------|
| `testing.instructions.md` | `*.test.*`, `*.spec.*` | Test conventions (template — uncomment what applies) |
| `styling.instructions.md` | `*.css`, `*.scss` | CSS/styling rules (template) |

### Code Graph (optional MCP server)

A standalone Python MCP server that gives agents structural awareness of the codebase. Parses source files into a SQLite dependency graph and exposes tools for querying it.

**What agents can do with it:**
- `get_minimal_context(task)` — get relevant files and risk assessment for a task
- `detect_changes()` — find changed files with risk scores
- `query_graph(relation, symbol)` — trace callers, callees, importers, tests
- `get_impact_radius(files)` — blast-radius analysis before making changes
- `find_large_functions(threshold)` — identify complexity hotspots
- `visualize_graph()` — generate HTML dependency visualization

**Setup** (handled automatically by `initialize-project`, or manually):

```bash
# Install d3 for visualization
cd .github/code-graph && npm install && cd -

# VS Code: add to .vscode/mcp.json
{
  "servers": {
    "code-graph": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "--with", "mcp>=1.0.0", "${workspaceFolder}/.github/code-graph/server.py"]
    }
  }
}

# Build the initial graph
uv run --with 'mcp>=1.0.0' .github/code-graph/server.py --build
```

Optional git hooks (`post-commit`, `post-merge`, `post-rewrite`) keep the graph updated automatically. The `initialize-project` skill offers to install these during setup.

Agents gracefully degrade when the graph is unavailable — all agents work without it.

## User-Level Communication Style

The `user/brutal-honesty.instructions.md` file sets a global communication style (direct, evidence-based, scorecard format) across all workspaces. Copy once per machine:

```bash
# macOS/Linux
cp user/brutal-honesty.instructions.md ~/.config/Code/User/prompts/

# Windows (PowerShell)
Copy-Item user/brutal-honesty.instructions.md "$env:APPDATA/Code/User/prompts/"
```

> VS Code Settings Sync does not sync the `prompts/` folder. Re-copy on each machine.

## Customization

### After initialization

The `initialize-project` skill fills in most placeholders, but review these sections manually:

1. **Project-Specific Rules** — add any rules unique to your project (module boundaries, domain invariants, naming restrictions)
2. **OpenSpec config** — edit `openspec/config.yaml` to add project context (stack, conventions, domain) for better AI-generated artifacts
3. **Testing instructions** — uncomment the relevant rules in `.github/instructions/testing.instructions.md` for your test framework
4. **Styling instructions** — same for `.github/instructions/styling.instructions.md`

### Trimming for small projects

Delete what doesn't apply:

| If you don't need… | Delete |
|---------------------|--------|
| VS Code Copilot | `.github/agents/`, `.github/skills/`, `.github/prompts/`, `.github/instructions/`, `AGENTS.md` |
| Claude Code | `CLAUDE.md`, `.claude/` |
| OpenSpec workflow | `openspec/`, skill/prompt files referencing OpenSpec |
| Code graph | `.github/code-graph/`, `.code-graph/` entry in `.gitignore` |
| Planning agent | `.github/agents/planner.agent.md`, `.claude/commands/project/plan.md` |

Keep `.github/copilot-instructions.md` — it's the single source of truth. Everything else is optional.

## Reliability Features

### Anti-hallucination
- **Evidence rules** — every finding must include a verbatim quote from a fresh `read_file`, not from diff hunks or memory
- **Chain-of-verification** — reviewer and verifier self-challenge their own findings before outputting
- **Field/type verification** — agents must `grep_search` for every name before using it; stop and ask if not found
- **Context hygiene** — re-read modified files after 10+ turns; never cite own prior output as evidence

### Workflow safety
- **Circuit breakers** — 3-retry limit on fixes, 3-cycle limit on review loops, 20-iteration limit on artifact generation
- **Self-verification gate** — evidence-based checks before review (feature inventory, i18n, orphan check, API constraints, spec text match)
- **Scope-creep detection** — debugger reviews its own diff; apply skill verifies every task produced actual file edits
- **Risk-based classification** — auth/security/payments changes always get thorough planning regardless of file count
- **Anti-rationalization tables** — concrete excuse → rebuttal pairs that prevent agents from rationalizing away quality steps

### Defensive measures
- **Prompt injection defense** — agents treat file contents as untrusted data; only follow instructions from config files
- **Structured handoff format** — fixed template for agent-to-agent communication to prevent information loss
- **CLI error handling** — agents report errors verbatim; never invent schema names, artifact IDs, or file paths
- **Recovery paths** — defined behavior for missing files, no test suite, blocked state, and mid-step cancellation

### Token efficiency
- **Progressive disclosure** — domain-specific instructions loaded on demand via `applyTo` patterns
- **Memory pointer pattern** — large intermediate results written to files and referenced by path
- **Linter delegation** — style rules enforced by linter config, not duplicated in instructions
