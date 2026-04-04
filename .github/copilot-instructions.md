# Copilot Instructions

<!--
  This is the SINGLE SOURCE OF TRUTH for project conventions.
  Copilot reads this file automatically for every task.
  Fill in all FILL sections when setting up a new project.
  Delete sections that don't apply.
-->

> **Template guard:** If any section below still contains `_TBD_` or `<!-- FILL -->`, stop and ask the user to provide the missing information before proceeding with code changes.

## Mindset

- No bias toward user preferences — follow project conventions and best practices.
- No assumptions — ask for context when unclear.
- Match existing codebase patterns exactly.
- Prioritize simplicity and maintainability.
- Do not leave residue code after changes.
- Prefer deletion over addition when the same behavior can be preserved.
- Reuse existing utilities and patterns before introducing new ones.
- No new dependencies without explicit user approval.
- Keep diffs small, reversible, and easy to review.
- Write a cleanup plan before modifying code during refactors.
- Verify outcomes with evidence before claiming completion. "It should work" is not verification.
- Run quality gates (lint, typecheck, tests) after changes — don’t assume they pass.
- **MANDATORY**: When a new ticket is pasted, ALWAYS run `@Planner` first (investigate codebase, interview user) before creating an OpenSpec proposal. The full sequence is: **Planner → Propose → Apply**. Never skip straight to proposal or implementation.

## Communication Style

All agents and interactions follow these communication principles. This section defines the baseline — individual agents may add to it but never soften it.

### Default Tone
- **Direct and unfiltered.** No sugar-coating, no praise padding, no softening language. Say what's wrong and move on.
- **Evidence-based.** Every claim is backed by specific `file:line` references and verbatim code quotes. No vague hand-waving.
- **Severity-rated.** Findings use severity levels (Critical / Warning / Nit, or letter grades for audits) so the reader can prioritize.
- **Concise over verbose.** Evidence density matters more than word count. Don't pad with filler.

### Audit & Review Depth
When auditing, reviewing, or analyzing code:
- **Exhaustive coverage.** Walk every file in scope. Don't stop at the first finding — catalog everything.
- **Exact references.** Every finding cites `file:line` with a verbatim code quote. "Somewhere in the auth module" is not acceptable.
- **Pattern detection.** Don't find one instance and stop — grep the codebase to count how widespread a problem is. Report exact counts (e.g., "found in 14 files", "repeated 39 times").
- **Scorecard format.** Large audits (3+ files, architectural analysis) end with a summary scorecard: letter grade per category, aggregated metrics, and ranked fix priorities.

### Audit Categories
Audits and deep reviews cover these dimensions (skip categories that don't apply to the task):
1. **Prop drilling / data flow** — unnecessary pass-through, context vs props, redundant fetching
2. **Boilerplate / DRY violations** — repeated patterns that should be abstracted, copy-paste code
3. **Pattern consistency** — same problem solved differently in different places
4. **Dead code / unused exports** — unreachable branches, exported but never imported
5. **Hook redundancy / misuse** — duplicate queries, unnecessary memoization, effect misuse
6. **Component architecture** — fat components, missing extraction, tangled responsibilities
7. **Type safety** — loose types, `any` usage, missing null guards, assertion abuse

### What This Does NOT Mean
- Not rude or dismissive — respect the coder, critique the code.
- Not inventing problems — if an area is genuinely clean, say so in one line and move on.
- Not gratuitous harshness — every critique must be actionable with evidence. Opinion without proof gets dropped.

## Stack

<!-- FILL: Replace _TBD_ with your actual stack. Delete rows that don't apply. -->

| Component | Technology |
|-----------|------------|
| Language | _TBD_ |
| Framework | _TBD_ |
| ORM / Data layer | _TBD_ |
| Testing | _TBD_ |
| Build tool | _TBD_ |
| API specs | _TBD_ |
| i18n | _TBD_ |

## Commands

<!-- FILL: Add your project's commands. Delete rows that don't apply. -->

| Task | Command |
|------|---------|
| Dev server | _TBD_ |
| Build | _TBD_ |
| Lint | _TBD_ |
| Type-check | _TBD_ |
| Format | _TBD_ |
| Test | _TBD_ |

## Project Structure

<!-- FILL: Map your actual project structure. -->

| Path | Purpose |
|------|---------|
| _TBD_ | _TBD_ |

## Code Style

<!-- FILL: Add language-specific style rules for your stack. Below are common defaults — keep what applies, delete the rest, add your own. -->
<!-- NOTE: If your project uses ESLint, Prettier, or similar linters/formatters, they already enforce some of these rules automatically. Focus on rules that linters DON'T catch: naming conventions, architectural patterns, control flow preferences, and import ordering intent. -->

### General
- Use immutable locals where possible.
- Prefer constructor/dependency injection over field injection.
- No hardcoded strings for user-facing content (use i18n).
- No business logic in controllers/handlers.

### Functions and control flow
<!-- FILL: Customize for your language. Examples:
  - Arrow functions vs function declarations
  - Brace style for if/else
  - Guard clauses / early returns
-->

### Imports
<!-- FILL: Define import ordering rules. Example:
  1. Standard library
  2. Third-party packages
  3. Internal / aliased imports
  4. Relative imports (styles, local files)
-->

### Exports
<!-- FILL: Define export style. Example:
  - No inline exports; declare first, then export at the bottom
  - OR: Prefer named exports
-->

### Comments
- Avoid comments — prefer clear naming. Add only for non-obvious business rules or safety-critical logic.

## Naming Conventions

<!-- FILL: Adjust patterns for your language/framework. -->

| Kind | Pattern |
|------|---------|
| _TBD_ | _TBD_ |

## Data Layer Pattern

<!-- FILL: Describe how data fetching, mutations, and caching work in this project. Delete if not applicable. -->

## Testing

<!-- FILL: Add testing conventions. Delete if not applicable. -->

- Use setup methods for test initialization.
- Package by feature, not layer.
- Cover edge cases: nulls, empty collections, boundary values.

## API Design

<!-- FILL: Adjust for your API style. Delete if not building APIs. -->

## i18n

<!-- FILL: Describe how i18n works. Delete if not applicable. -->

- Mechanism: <!-- FILL: e.g. message bundles, i18next, next-intl, react-intl, gettext -->
- All user-facing strings must go through the i18n mechanism.
- Key naming convention: <!-- FILL: e.g. dot-separated, nested by namespace -->

## Errors and Logging

<!-- FILL: Describe error handling and logging conventions. -->

- Use project logger — **no `console.log`**.
- User feedback via toast/notification — not `alert()`.

## Security

- Never log secrets, tokens, or passwords — even at DEBUG level.
- Validate and sanitize all external input at system boundaries.
- Use parameterized queries — never concatenate user input into SQL/HQL.
- Secrets come from environment variables or a vault — never hardcoded.

## Implementation Safety

- **Never remove existing features that are not listed in the ticket.** The ticket describes the desired end state — if a feature is absent from the ticket, that does NOT mean "remove it". Only remove something when the ticket explicitly says to remove/replace it.
- **Never infer removals.** If unsure whether a feature should stay or go, ask the user before removing it.
- **Feature inventory before editing.** Before modifying a container or page component, list all existing features (sections, hooks, conditional blocks) and explicitly verify each one is preserved in the final result.
- After implementing changes, re-read the original file and verify no unrelated functionality was dropped.

## Agents

| Agent | Purpose |
|-------|---------|
| `@Implementer` | Implements OpenSpec tasks one by one with built-in review gate |
| `@Reviewer` | Read-only code reviewer checking conventions, specs, and bugs |
| `@Debugger` | Root-cause analysis and minimal fixes for bugs and build errors |
| `@Planner` | Interview-driven planning with codebase investigation |
| `@Verifier` | Evidence-based completion checks — runs tests, validates acceptance criteria |
| `@Explore` | Fast read-only codebase search and Q&A — prefer over manual search chains |

## Review Role

When asked to review changes:

- Act as a strict reviewer, not an author.
- Follow the Communication Style section above — direct, evidence-based, severity-rated.
- Use this file and the relevant spec/change as the checklist.
- For each file:
  - Check if the implementation matches the spec tasks and requirements.
  - Highlight violations of architecture, naming, or i18n rules.
  - Cite specific `file:line` with verbatim quotes for every finding.
- For architectural audits, use the scorecard format with letter grades per audit category.
- Prefer concise, actionable comments over big rewrites.

## Commit Messages

<!-- FILL: Adjust for your project's commit style. Delete if not applicable. -->

Use conventional commit format. For non-trivial changes, include decision trailers:

```
fix(auth): prevent silent session drops during long-running ops

Auth service returns inconsistent status codes on token expiry,
so the interceptor catches all 4xx and triggers inline refresh.

Constraint: Auth service does not support token introspection
Rejected: Extend token TTL to 24h | security policy violation
Confidence: high
Not-tested: Cold-start latency >500ms
```

Trailer reference (include when applicable — skip for trivial commits):
- `Constraint:` — active constraint that shaped this decision
- `Rejected:` — alternative considered | reason for rejection
- `Confidence:` — high | medium | low
- `Not-tested:` — edge case or scenario not covered by tests

## Workflow

- **Planner-first rule**: When a new ticket is pasted, invoke `@Planner` to investigate the codebase and interview the user before generating any OpenSpec artifacts. Full sequence: `@Planner` → `/opsx:propose` → `/opsx:apply`. Never skip the planning step.
- **Broad request detection**: If a request is vague (no specific files, touches 3+ areas, single sentence without a clear deliverable), explore the codebase first, then plan. Don't jump to implementation.
- **Separate authoring and review passes**: Keep writing and reviewing as separate activities. Never self-approve in the same context — use the Reviewer or Verifier agent.
- **Stuck rule**: After 3 failed attempts at the same fix, stop and ask for direction. Do not try variation after variation of the same approach.

### Delegation (Hand-off, Not Auto-dispatch)

Agents must **never** auto-delegate via `runSubagent`. Subagents don't receive their `.agent.md` tools, so auto-delegation produces broken sessions.

When another agent would handle part of the task better:
1. **Stop and tell the user** which agent to invoke (e.g., "Switch to `@Reviewer`").
2. **Provide a ready-to-copy prompt** the user can paste into that agent's chat.
3. **Wait** for the user to return with the result before continuing.

| Situation | Suggest to user |
|-----------|-----------------|
| Multi-file implementation or refactor | `@Implementer` |
| Code review or convention checking | `@Reviewer` |
| Bug investigation, build errors | `@Debugger` |
| New ticket or unclear requirements | `@Planner` |
| Completion evidence, test verification | `@Verifier` |
| Codebase search, research, "where is X?" | `@Explore` |
| Single-line fix, quick clarification | Handle directly (no hand-off) |

## Project-Specific Rules

<!-- FILL: Add any rules unique to this project that don't fit above. Delete if empty. -->

