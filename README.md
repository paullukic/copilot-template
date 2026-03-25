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
.github/
  copilot-instructions.md                    # Project conventions (single source of truth)
  agents/
    implementer.agent.md                     # OpenSpec task implementer with review gate
    reviewer.agent.md                        # Strict code reviewer agent
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

Then ask Copilot: "Read the README and set up my project."

## What's Included

### `.github/copilot-instructions.md` (template)
The single source of truth for project conventions. Has `<!-- FILL -->` and `_TBD_` markers for: tech stack, commands, project structure, code style, naming, data layer, testing, API design, i18n, logging, security, and implementation safety rules. Copilot reads this automatically.

### `AGENTS.md` (template)
A brief summary for multi-editor compatibility (Cursor, Windsurf, etc.). Points to `copilot-instructions.md` as the full reference.

### Agents

- **Implementer** — Executes OpenSpec tasks methodically. Has Cardinal Rules (tasks.md is the work order, read before writing, never invent fields, make real edits) and a Self-Verification Gate (feature inventory, i18n completeness, orphan check, API constraint check, spec text match) before review.
- **Reviewer** — Strict read-only code reviewer. Checks spec compliance, project conventions, data layer patterns, deep bugs (control flow, null paths, edge cases), simplicity, and cross-module impact.

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

1. **Propose**: Describe what you want to build → `/opsx:propose add-dark-mode`
2. **Explore** (optional): Think through problems → `/opsx:explore`
3. **Implement**: Work through tasks → `/opsx:apply`
4. **Archive**: Finalize when done → `/opsx:archive`
