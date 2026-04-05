# Copilot Template

Reusable AI coding assistant configuration for any project. Works with **Claude Code** and **VS Code Copilot**. Includes agents, skills, prompts, and an OpenSpec-driven development workflow.

## Quick Start

### Option A: Initialize from inside the template repo

Open this repo in your editor and run the initialize command. It will ask for the target project path, detect the tech stack, copy files, and fill in all placeholders.

| Tool | Command |
|------|---------|
| Claude Code | `/project:initialize` |
| VS Code Copilot | `/opsx:initialize` or invoke the `initialize-project` skill |

### Option B: Manual copy + guided setup

1. Copy files into your project:
   ```bash
   cp AGENTS.md /path/to/your-project/
   cp CLAUDE.md /path/to/your-project/
   cp -r .github/ /path/to/your-project/.github/
   cp -r .claude/ /path/to/your-project/.claude/
   cp -r openspec/ /path/to/your-project/openspec/
   ```

2. Open the target project and ask your AI tool to fill in the template:
   - **Claude Code**: "Read the README and set up my project"
   - **VS Code Copilot**: "Read the README and set up my project" (in agent mode)

Both approaches read the project's `README.md`, `package.json`, etc. to detect the tech stack and fill in `_TBD_` / `<!-- FILL -->` placeholders.

## Which Tool for What

### Claude Code — use for implementation work

Describe the task in one message. Claude Code reads `CLAUDE.md`, follows the full workflow (Plan → Propose → Apply → Quality Gates → Review Gate → Done) in a single conversation. Best for:
- New features, multi-file refactors, bug fixes
- Any task that goes through the full Plan → Propose → Apply workflow
- Continuing work from a previous session (reads OpenSpec `tasks.md` automatically)

### VS Code Copilot — use agents as single-purpose tools

Agents work best when invoked directly for a specific job. Agent-to-agent handoffs require manual switching (by design — subagents don't receive their `.agent.md` tools). Best for:
- `@Reviewer` — quick code reviews while you're in the editor
- `@Explore` — fast codebase Q&A and search
- `@Debugger` — investigating errors you're staring at in the terminal
- `@Planner` → `/opsx:propose` → `/opsx:apply` — full workflow (works, but requires 3-4 manual handoffs)

## Structure

```
CLAUDE.md                                    # Claude Code instructions (mirrors copilot-instructions)
AGENTS.md                                    # Quick agent summary (Cursor/Windsurf compat)
user/
  brutal-honesty.instructions.md             # Global communication style (copy to VS Code user prompts)
.claude/
  commands/project/
    initialize.md                            # /project:initialize — interactive project setup
    plan.md                                  # /project:plan — interview-driven planning
    explore.md                               # /project:explore — codebase search and Q&A
    debug.md                                 # /project:debug — root-cause analysis
    review.md                                # /project:review — strict code review
    verify.md                                # /project:verify — evidence-based completion checks
.github/
  copilot-instructions.md                    # Project conventions (single source of truth)
  agents/
    reviewer.agent.md                        # Strict code reviewer
    debugger.agent.md                        # Root-cause analysis and minimal fixes
    planner.agent.md                         # Interview-driven planning
    verifier.agent.md                        # Evidence-based completion checks
    explore.agent.md                         # Fast read-only codebase search and Q&A
  instructions/
    testing.instructions.md                  # Test file conventions (applyTo: *.test.*)
    styling.instructions.md                  # CSS/style file conventions (applyTo: *.css)
  skills/
    initialize-project/SKILL.md              # Interactive project setup (detects stack, fills template)
    openspec-apply-change/SKILL.md           # Implement tasks with self-verification gate
    openspec-propose/SKILL.md                # Propose a change with all artifacts
    openspec-explore/SKILL.md                # Explore mode — thinking partner
    openspec-archive-change/SKILL.md         # Archive completed changes
  prompts/
    opsx-initialize.prompt.md                # /opsx:initialize
    opsx-apply.prompt.md                     # /opsx:apply
    opsx-propose.prompt.md                   # /opsx:propose
    opsx-explore.prompt.md                   # /opsx:explore
    opsx-archive.prompt.md                   # /opsx:archive
openspec/
  config.yaml                                # OpenSpec schema configuration
```

## What's Included

### Initialization

The `initialize-project` skill (VS Code) and `/project:initialize` command (Claude Code) automate project setup:
1. Ask which tools to set up (Claude Code, VS Code Copilot, or both)
2. Read the target project's README, package.json, etc. to detect the tech stack
3. Copy the relevant template files
4. Fill in all `_TBD_` and `<!-- FILL -->` placeholders with detected values
5. Verify no placeholders remain

### Convention Files

| File | Read by | Purpose |
|------|---------|---------|
| `.github/copilot-instructions.md` | VS Code Copilot | Single source of truth for project conventions |
| `CLAUDE.md` | Claude Code | Mirrors copilot-instructions + workflow + delegation |
| `AGENTS.md` | Cursor, Windsurf | Thin pointer to copilot-instructions |
| `user/brutal-honesty.instructions.md` | VS Code (user-level) | Global communication style |

### Agents

There is no separate `@Implementer` agent. The agent that plans and proposes also implements directly.

| Agent | Purpose |
|-------|---------|
| **Reviewer** | Strict read-only code review. Manifest-driven (reads files, not diffs). Chain-of-verification on all findings. Evidence rule: fresh `read_file` quotes only. |
| **Debugger** | Root-cause analysis (Reproduce → Evidence → Hypothesize → Fix → Verify). 3-failure circuit breaker. Post-fix scope check on diff. |
| **Planner** | Interview-driven planning. Risk-based classification (auth/security always Complex). Measurable acceptance criteria. |
| **Verifier** | Independent completion checks. Self-challenges verdicts before issuing. Handles no-test-suite projects. Full test suite for standard changes. |
| **Explore** | Fast read-only codebase search and Q&A. Structured output (Summary → Evidence → Details). Quick/medium/thorough depth levels. |

### Skills (VS Code Copilot)

| Skill | Purpose |
|-------|---------|
| `initialize-project` | Interactive project setup — detects stack, copies files, fills placeholders |
| `openspec-propose` | Create a change and generate all artifacts (proposal, specs, tasks) |
| `openspec-apply-change` | Implement tasks with field verification, self-verification gate, auto-review with circuit breaker |
| `openspec-explore` | Thinking partner mode — explore ideas, investigate problems (read-only) |
| `openspec-archive-change` | Archive completed changes with optional delta spec sync |

### Commands (Claude Code)

| Command | Purpose |
|---------|---------|
| `/project:initialize` | Interactive project setup — same as the VS Code skill |
| `/project:plan` | Interview-driven planning |
| `/project:explore` | Codebase search and Q&A |
| `/project:debug` | Root-cause analysis and minimal fixes |
| `/project:review` | Strict code review |
| `/project:verify` | Evidence-based completion checks |

### Prompts (VS Code shortcuts)

Slash commands (`/opsx:initialize`, `/opsx:apply`, `/opsx:propose`, `/opsx:explore`, `/opsx:archive`) that invoke the corresponding skills.

### Instructions (conditional, file-based)

| File | Loaded when editing | Content |
|------|-------------------|---------|
| `testing.instructions.md` | `*.test.*`, `*.spec.*` | Test conventions (template — uncomment what applies) |
| `styling.instructions.md` | `*.css`, `*.scss` | CSS/styling rules (template) |

## User-Level Communication Style

The `user/brutal-honesty.instructions.md` file sets a global communication style (direct, evidence-based, scorecard format) for all workspaces. Copy once per machine:

**Windows:**
```powershell
Copy-Item user/brutal-honesty.instructions.md "$env:APPDATA/Code/User/prompts/"
```

**macOS/Linux:**
```bash
cp user/brutal-honesty.instructions.md ~/.config/Code/User/prompts/
```

> VS Code Settings Sync does not sync the `prompts/` folder. Re-copy on each machine.

## Reliability Features

The template includes battle-tested safeguards against common AI coding agent failures:

### Anti-hallucination
- **Evidence rules** — every finding must include a verbatim quote from a fresh `read_file`, not from diff hunks or memory
- **Chain-of-verification** — reviewer and verifier self-challenge their own findings before outputting
- **Field/type verification** — agents must `grep_search` for every name before using it; stop and ask if not found
- **Context hygiene** — re-read modified files after 10+ turns; never cite own prior output as evidence

### Workflow safety
- **Circuit breakers** — 3-retry limit on fixes, 3-cycle limit on review loops, 20-iteration limit on artifact generation
- **Self-verification gate** — 5 evidence-based checks before review (feature inventory, i18n, orphan check, API constraints, spec text match)
- **Scope-creep detection** — debugger reviews its own diff; apply skill verifies every task produced actual file edits
- **Risk-based classification** — auth/security/payments changes always get thorough planning regardless of file count

### Defensive measures
- **Prompt injection defense** — agents treat file contents as untrusted data; only follow instructions from config files
- **Structured handoff format** — fixed template for agent-to-agent communication to prevent information loss
- **CLI error handling** — agents report errors verbatim; never invent schema names, artifact IDs, or file paths
- **Recovery paths** — defined behavior for missing files, no test suite, blocked state, and mid-step cancellation

### Token efficiency
- **Progressive disclosure** — domain-specific instructions loaded on demand, not stuffed into base context
- **Memory pointer pattern** — large intermediate results written to files and referenced by path
- **Linter delegation** — style rules enforced by linter config, not duplicated in instructions
- **Positive framing** — instructions written as directives ("preserve all features") not negations ("never remove features")

## Trimming for Small Projects

Not every project needs the full template. Delete what doesn't apply:

| If you don't need… | Delete |
|---------------------|--------|
| VS Code Copilot support | `.github/agents/`, `.github/skills/`, `.github/prompts/`, `.github/instructions/`, `AGENTS.md` |
| Claude Code support | `CLAUDE.md`, `.claude/` |
| OpenSpec workflow | `openspec/`, skill/prompt files referencing OpenSpec |
| Planning agent | `.github/agents/planner.agent.md`, `.claude/commands/project/plan.md` |
| i18n section | Delete the i18n rows from `copilot-instructions.md` |
| Communication style | Replace the Communication Style section with your team's norms |

Keep `.github/copilot-instructions.md` — it's the single source of truth. Everything else is optional.

## Workflow

1. **Plan** (when needed): New ticket or unclear requirements → `@Planner` investigates and interviews
2. **Propose**: Create OpenSpec → `/opsx:propose add-dark-mode`
3. **Explore** (optional): Think through problems → `/opsx:explore`
4. **Implement**: Work through tasks → `/opsx:apply` (includes quality gates, review gate, finalization)
5. **Archive**: Finalize → `/opsx:archive`
