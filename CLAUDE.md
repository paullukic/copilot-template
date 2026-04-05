# Claude Code Instructions

Read `.github/copilot-instructions.md` at the start of every implementation task. It contains all project conventions, code style, data layer patterns, i18n rules, and agent configuration.

Domain-specific instructions (testing, styling) are in `.github/instructions/` and are loaded automatically by VS Code when editing matching files. For Claude Code, read them on demand: check `.github/instructions/testing.instructions.md` when writing tests, `.github/instructions/styling.instructions.md` when writing CSS.

## Communication Style

Follow the communication style defined in `.github/copilot-instructions.md` — direct, evidence-based, concise. No filler, no praise padding, no softening.

## Quick Reference

| Task | Command |
|------|---------|
| Dev server | `_TBD_` |
| Build | `_TBD_` |
| Lint | `_TBD_` |
| Type-check | `_TBD_` |
| Format | `_TBD_` |
| Test | `_TBD_` |

## Branching Strategy

## Key Paths

- Source code: `src/`
- Shared components: `_TBD_`
- API types: `_TBD_`
- Translations: `_TBD_`
- Navigation index: `_TBD_`

## Critical Rules (from copilot-instructions — surfaced here because they cause the most damage when missed)

- **Regenerate API types** using the appropriate command. Editing generated types directly will be overwritten.
- **Preserve all existing features** unless the ticket explicitly says to remove them. A feature absent from the ticket means "keep it." When in doubt, ask.
- **Feature inventory before editing.** Before modifying a container or page, list all existing features (sections, hooks, conditional blocks, admin-only UI) and verify each is preserved in the final result.
- **No new dependencies** without explicit user approval.

## Implementation Workflow (MANDATORY)

Before any non-trivial implementation, follow: **Plan → Propose → Apply**. Never skip straight to writing code. Full rules are in `.github/copilot-instructions.md` § Workflow — read that section. Summary below.

### When the workflow does NOT apply

- **Review only** — deliver the review and stop.
- **Exploration / research** — answer the question, not an implementation task.
- **Single-file fixes, typos, trivial changes** — just do it.

### Step 1: Plan

- **Run `/project:plan`** for new tickets, unclear requirements, or non-obvious scope.
- **Skip planning** when review output already exists in conversation, or the user specifies the problem, files, and fix direction.
- **Bug reports**: Run `/project:debug`. If fix is trivial, just fix it. If multi-file, go to Step 2.

### Step 2: Propose (OpenSpec)

Create an OpenSpec in `openspec/changes/<date>-<slug>/` with `.openspec.yaml`, `proposal.md`, `specs/<capability>/spec.md`, and `tasks.md`.

`proposal.md` sections: Why, Goals/Non-Goals, Decisions, Impact, Risks.

`tasks.md`: group by logical unit (not per-file), final group is verification, each task independently verifiable.

See `openspec/changes/archive/` for reference. **Wait for user approval** before implementing.

### Step 3: Apply

- Work through `tasks.md` in order. Mark tasks done as you go.
- Read every file before editing. Check API spec / generated types before assuming names.
- If you hit a non-obvious build error, run `/project:debug`.
- Mid-implementation requirement changes: update the OpenSpec, then continue.
- Continuing previous work: check `openspec/changes/` for in-progress OpenSpec.

**After all tasks are done:**

1. **Quality gates** — run typecheck, lint, format. Fix until clean.
2. **Finalization checklist** — read `.github/copilot-instructions.md` § "Checklist before finalizing" and run every item.
3. **Review gate** — run `/project:review`. Fix Critical/Warning findings. Re-run quality gates after fixes. Re-review only if fixes were substantial.
4. **Done** — declare completion, ask user for next steps.

### Archiving

Move completed OpenSpecs from `openspec/changes/<slug>/` to `openspec/changes/archive/<slug>/`.

## Subagent Delegation

| Situation | Command |
|-----------|---------|
| Code review or convention audit | `/project:review` |
| Bug investigation, build errors | `/project:debug` |
| Planning / unclear requirements | `/project:plan` |
| Completion evidence, verification | `/project:verify` |
| Codebase search, research | `/project:explore` |

Pass the full task description and relevant file paths when delegating.

## Context Management

### Preservation on compaction
When the conversation context is compacted, always preserve:
- The current task from `tasks.md` (if working through an OpenSpec)
- The full list of files modified in this session
- Any failing test or build output not yet resolved
- Acceptance criteria for the current task
- Any user decisions or scope changes made during this session

### Memory pointer pattern
When intermediate results are large (investigation findings, audit reports, dependency maps), write them to a file in the OpenSpec change directory (e.g., `openspec/changes/<name>/notes/<topic>.md`) and reference the file path in conversation instead of keeping the full content in context. This prevents context overflow on complex tasks and preserves findings across conversation compaction.

### Context hygiene
Long conversations accumulate stale state. To prevent acting on outdated information:
- **After every 10+ turns of implementation**: re-read all files you've modified from disk. Your memory of their contents may have drifted from reality.
- **Never cite your own prior output as evidence.** Only fresh `read_file` / tool output counts. If you said "line 42 has X" five turns ago, re-read line 42 before acting on it.
- **When conversation history contradicts a file on disk**, trust the file. The file is the source of truth — conversation history may contain hallucinations that got referenced and compounded.
