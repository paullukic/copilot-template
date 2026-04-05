# Copilot Template

Reusable VS Code Copilot customization files for any project. Includes agents, skills, and prompts for an OpenSpec-driven development workflow.

## For Copilot: Bootstrap Instructions

When a user adds this template to a new project and asks you to set it up:

1. **Read `.github/copilot-instructions.md`** and find all sections marked with `<!-- FILL: ... -->` or `_TBD_`.
2. **Ask the user** for the missing information. Group your questions:
   - Tech stack (language, framework, ORM, build tool, test framework)
   - Commands (dev, build, lint, format, test)
   - Project structure
   - Code style preferences (imports, exports, functions)
   - Naming conventions
   - Any project-specific rules
3. **Fill in the sections** with the answers. Remove the `<!-- FILL: ... -->` comments and `_TBD_` placeholders.
4. **Delete sections** the user says don't apply (e.g., no i18n, no API design).
5. **Update `AGENTS.md`** with a brief stack and structure summary.
6. **Confirm** the final setup with the user.

If the user says "read the README" or "set up my project", this is what they mean.

## Structure

```
AGENTS.md                                    # Quick agent summary (Cursor/Windsurf compat)
user/
  brutal-honesty.instructions.md             # Global communication style (copy to VS Code user prompts)
.github/
  copilot-instructions.md                    # Project conventions (single source of truth)
  agents/
    reviewer.agent.md                        # Strict code reviewer agent
    debugger.agent.md                        # Root-cause analysis and minimal fixes
    planner.agent.md                         # Interview-driven planning
    verifier.agent.md                        # Evidence-based completion checks
    explore.agent.md                         # Fast read-only codebase search and Q&A
  instructions/
    testing.instructions.md                  # Test file conventions (applyTo: *.test.*)
    styling.instructions.md                  # CSS/style file conventions (applyTo: *.css)
  skills/
    openspec-apply-change/SKILL.md           # Implement tasks with self-verification gate
    openspec-propose/SKILL.md                # Propose a change with all artifacts
    openspec-explore/SKILL.md                # Explore mode — thinking partner
    openspec-archive-change/SKILL.md         # Archive completed changes
  prompts/
    opsx-apply.prompt.md                     # Quick prompt: /opsx:apply
    opsx-propose.prompt.md                   # Quick prompt: /opsx:propose
    opsx-explore.prompt.md                   # Quick prompt: /opsx:explore
    opsx-archive.prompt.md                   # Quick prompt: /opsx:archive
openspec/
  config.yaml                                # OpenSpec schema configuration
```

## Setup

Copy into a new project:

```bash
cp AGENTS.md /path/to/your-project/
cp -r .github/ /path/to/your-project/.github/
cp -r openspec/ /path/to/your-project/openspec/
```

Then ask Copilot: "Read the README and set up my project." (Requires Copilot Chat in agent mode.)

### User-Level Communication Style (per machine — portable via this repo)

The `user/brutal-honesty.instructions.md` file defines a global communication style (direct, evidence-based, scorecard format) that applies to ALL workspaces on a machine. Copy it to your VS Code user prompts folder:

**Windows:**
```powershell
Copy-Item user/brutal-honesty.instructions.md "$env:APPDATA/Code/User/prompts/"
```

**macOS/Linux:**
```bash
cp user/brutal-honesty.instructions.md ~/.config/Code/User/prompts/
```

This only needs to be done once per machine. Since this file lives in the template repo, when you update it and `git pull` on another machine, just re-copy it.

> **Note:** If you use VS Code Settings Sync, the `prompts/` folder is NOT synced automatically. The copy step is required on each machine.

## What's Included

### `.github/copilot-instructions.md` (template)
The single source of truth for project conventions. Has `<!-- FILL -->` and `_TBD_` markers for: tech stack, commands, project structure, code style, naming, data layer, testing, API design, i18n, logging, security, and implementation safety rules. Includes a **Communication Style** section that enforces direct, evidence-based, severity-rated communication across all agents. Copilot reads this automatically.

### `user/brutal-honesty.instructions.md`
A VS Code user-level instruction file that applies the communication style globally (all workspaces, all conversations). Copy to your VS Code user prompts folder once per machine. This ensures the style follows you even in projects not bootstrapped from this template.

### `AGENTS.md` (template)
A brief summary for multi-editor compatibility (Cursor, Windsurf, etc.). Points to `copilot-instructions.md` as the full reference.

> **Why both files?** VS Code Copilot reads `.github/copilot-instructions.md` automatically. Cursor and Windsurf read `AGENTS.md` instead. Both files exist so the template works across editors. `copilot-instructions.md` is the source of truth; `AGENTS.md` is a thin pointer that avoids duplication.

### Agents

There is no separate `@Implementer` agent. The agent that plans and proposes also implements directly.

- **Reviewer** — Strict read-only code reviewer. Checks spec compliance, project conventions, data layer patterns, deep bugs (control flow, null paths, edge cases), simplicity, and cross-module impact. Evidence rule: every finding must include a verbatim quote from tool output.
- **Debugger** — Root-cause analysis with a structured investigation protocol (Reproduce → Gather Evidence → Hypothesize → Fix → Verify). Has a 3-failure circuit breaker: after 3 failed hypotheses, stop and ask for direction.
- **Planner** — Interview-driven planning that investigates the codebase first (never asks users about codebase facts). Produces 3-8 step plans with acceptance criteria. Never implements — hands off to `/opsx:propose` → `/opsx:apply`.
- **Verifier** — Independent evidence-based completion checks. Runs tests/builds itself, verifies against acceptance criteria, and rejects claims without fresh output. Uses sized verification (small/standard/large). Separate from Reviewer (verifies completion, not style).
- **Explore** — Fast read-only codebase search and Q&A subagent. Supports quick/medium/thorough depth levels. Prefer over manually chaining search and file-read operations.

### Instructions (file-based, conditional)

Files in `.github/instructions/` are loaded on-demand based on `applyTo` glob patterns:
- **testing.instructions.md** — Loaded when editing `*.test.*` or `*.spec.*` files. Template with common test conventions (commented out — uncomment what applies).
- **styling.instructions.md** — Loaded when editing `*.css` or `*.scss` files. Template with CSS/styling rules.

### Skills

- **openspec-apply-change** — Implements tasks from an OpenSpec change with auto-review gate and self-verification.
- **openspec-propose** — Creates a change and generates all artifacts (proposal, design, tasks) in one step.
- **openspec-explore** — Thinking partner mode for exploring ideas, investigating problems, and clarifying requirements. Read-only — never implements code.
- **openspec-archive-change** — Archives completed changes with delta spec sync assessment.

### Prompts

Slash-command shortcuts (`/opsx:apply`, `/opsx:propose`, `/opsx:explore`, `/opsx:archive`) that invoke the corresponding skills with a streamlined interface.

### OpenSpec Config

Default `spec-driven` schema with commented examples for project context and per-artifact rules.

## Workflow

1. **Plan** (when needed): New ticket or unclear requirements → `@Planner` investigates and interviews. Skip when review findings already exist or scope is clear.
2. **Propose**: Create OpenSpec with `proposal.md`, specs, and `tasks.md` → `/opsx:propose add-dark-mode`
3. **Explore** (optional): Think through problems → `/opsx:explore`
4. **Implement**: Work through tasks → `/opsx:apply`. Includes quality gates, review gate, and finalization.
5. **Archive**: Finalize when done → `/opsx:archive`
