# Claude Code Instructions

Read `.github/copilot-instructions.md` at the start of every implementation task. It contains all project conventions, code style, data layer patterns, i18n rules, and agent configuration.

## Communication Style

Follow the communication style defined in `.github/copilot-instructions.md` at all times — not just during reviews. Direct, evidence-based, concise. No filler, no praise padding, no softening.

## Quick Reference

<!-- FILL: Add your project's common commands here -->

| Task | Command |
|------|---------|
| Dev server | `_TBD_` |
| Build | `_TBD_` |
| Lint | `_TBD_` |
| Type-check | `_TBD_` |
| Format | `_TBD_` |
| Test | `_TBD_` |

## Branching Strategy

<!-- FILL: e.g. "Always create new branches from dev, not from main." -->

## Key Paths

<!-- FILL: Add your project's key directories here -->

- Source code: `src/`
- Shared components: `_TBD_`
- API types: `_TBD_`
- Translations: `_TBD_`
- Navigation index: `_TBD_`

## Critical Rules (from copilot-instructions — surfaced here because they cause the most damage when missed)

<!-- FILL: Add project-specific critical rules. Examples below — keep what applies, delete what doesn't. -->

- **Never edit generated API types.** Regenerate with the appropriate command.
- **Never remove existing features** unless the ticket explicitly says to. If a feature is absent from the ticket, that does NOT mean "remove it." When in doubt, ask.
- **Feature inventory before editing.** Before modifying a container or page, list all existing features (sections, hooks, conditional blocks, admin-only UI) and verify each is preserved in the final result.
- **No new dependencies** without explicit user approval.

## Implementation Workflow (MANDATORY)

Before any non-trivial implementation (multi-file refactors, new features, review-finding fixes, bug fixes touching 3+ files), follow this sequence. **Never skip straight to writing code.**

### When the workflow does NOT apply

These tasks do not trigger the implementation workflow:
- **Review only** — user asks for a review or runs `/project:review`. Deliver the review and stop. Don't start planning or proposing unless the user asks to fix something.
- **Exploration / research** — user asks "where is X?", "how does Y work?", or runs `/project:explore`. Answer the question. Not an implementation task.
- **Single-file fixes, typos, trivial changes** — fix is self-evident. Just do it.

### Step 1: Plan

Understand the problem before proposing a solution.

**When to run `/project:plan`:**
- New tickets pasted by the user
- Unclear or ambiguous requirements
- Tasks where scope, affected files, or approach is not obvious

**When to skip `/project:plan`:**
- The current conversation already contains `/project:review` output AND the user asks to fix a finding from it. The review output IS the investigation — go straight to Step 2.
- The user explicitly pastes review findings or analysis from a previous session and asks to fix them.
- Refactors with clear scope where the user specifies the problem, affected files, and fix direction (e.g., "replace X pattern with Y across these files").

If none of these apply, run `/project:plan`. When in doubt, plan.

**Bug reports:** User says "this is broken." Run `/project:debug` to diagnose. Once the cause is identified: if the fix is trivial (1-2 files, obvious change), just fix it. If multi-file or architectural, go through Step 2 → Step 3.

**What planning produces:**
- List of affected files and their roles
- Clarifying questions for the user (ask before proposing — don't assume)
- Understanding of existing patterns to follow

### Step 2: Propose (OpenSpec)

Create an OpenSpec in `openspec/changes/<date>-<slug>/` with these artifacts:

| File | Purpose |
|------|---------|
| `.openspec.yaml` | `schema: spec-driven` + `created: <date>` |
| `proposal.md` | Single document: Why, Goals/Non-Goals, Decisions, Impact, Risks |
| `specs/<capability>/spec.md` | Requirements with BDD scenarios (WHEN/THEN) |
| `tasks.md` | Numbered task groups with checkboxes |

**proposal.md sections:**
- **Why** — the problem or motivation. Link to review findings, tickets, or user request.
- **Goals / Non-Goals** — what's in scope and explicitly what's not.
- **Decisions** — key design choices with rationale. Reference existing patterns to follow.
- **Impact** — list every file that will be created, modified, or deleted.
- **Risks** — what could go wrong and how it's mitigated.

**tasks.md rules:**
- Group by logical unit, not per-file. "Update all 12 section components to use useFormContext" = 1 task, not 12.
- Final task group is always verification (typecheck, lint, format).
- Each task should be independently verifiable.

See `openspec/changes/archive/` for reference examples. No separate `design.md` — everything goes in `proposal.md`.

**Wait for user approval** before proceeding to implementation. If the user requests changes, update the OpenSpec and re-present.

### Step 3: Apply (we implement directly)

There is no separate implementer agent. We implement directly.

**Implementation rules:**
- Work through `tasks.md` in order. Mark tasks done as you go.
- Read every file before editing it. Never edit a file you haven't read in this session.
- Check the API spec / generated types before assuming field names or types.
- After each logical group of changes, verify the code still compiles mentally — don't wait until the end to discover cascading type errors.
- If you hit an unexpected build error or runtime bug during implementation, run `/project:debug` to diagnose rather than guessing at fixes. Use `/project:debug` for non-obvious failures; fix obvious ones (missing imports, typos) inline.

**Mid-implementation requirement changes:** If the user adds or changes requirements during Step 3, update `proposal.md` and `tasks.md` in the OpenSpec to reflect the change, then continue implementation. Don't silently absorb scope changes — record them.

**Continuing work from a previous session:** If the user asks to continue a previous task, check `openspec/changes/` for an in-progress OpenSpec (not archived). Read its `tasks.md` to see what's done and what remains. If no OpenSpec exists, ask the user for context.

**After all tasks are done:**

1. **Quality gates** — run typecheck, lint, format (see Quick Reference for commands). If any fail, fix the errors and re-run until all pass clean. If a failure is not obvious, run `/project:debug` to diagnose before attempting a fix.
2. **Finalization checklist** — read `.github/copilot-instructions.md` § "Checklist before finalizing" and run every item. Do not run from memory — read the section first, then execute each check.
3. **Review gate** — run `/project:review` against the changes. The review checks implementation against the spec, project conventions, and copilot-instructions.
4. **Fix findings** — address any Critical or Warning findings from the review. After fixing, re-run quality gates (step 1). Then re-run `/project:review` only if the fixes were substantial (new files, changed architecture, modified public interfaces). Skip re-review for trivial fixes (typos, missing imports, formatting).
5. **Done** — declare completion and ask the user for next steps (e.g., commit and push, archive the OpenSpec, move on to the next task).

### Archiving

When the user asks to archive an OpenSpec, move it from `openspec/changes/<slug>/` to `openspec/changes/archive/<slug>/`.

## Subagent Delegation

You may spawn `claude` subprocesses to delegate work. Use the slash commands as a guide for what each role does:

| Situation | Command |
|-----------|---------|
| Code review or convention audit | `/project:review` |
| Bug investigation, build errors | `/project:debug` |
| Planning / unclear requirements | `/project:plan` |
| Completion evidence, verification | `/project:verify` |
| Codebase search, research | `/project:explore` |

When delegating, pass the full task description and any relevant file paths to the subprocess. The subprocess has full tool access and reads this file automatically.
