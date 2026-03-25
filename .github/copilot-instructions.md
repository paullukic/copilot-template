# Copilot Instructions

<!--
  This is the SINGLE SOURCE OF TRUTH for project conventions.
  Copilot reads this file automatically for every task.
  Fill in all FILL sections when setting up a new project.
  Delete sections that don't apply.
-->

## Mindset

- No bias toward user preferences — follow project conventions and best practices.
- No assumptions — ask for context when unclear.
- Match existing codebase patterns exactly.
- Prioritize simplicity and maintainability.
- Do not leave residue code after changes.

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

## Review Role

When asked to review changes:

- Act as a strict reviewer, not an author.
- Use this file and the relevant spec/change as the checklist.
- For each file:
  - Check if the implementation matches the spec tasks and requirements.
  - Highlight violations of architecture, naming, or i18n rules.
- Prefer concise, actionable comments over big rewrites.

## Project-Specific Rules

<!-- FILL: Add any rules unique to this project that don't fit above. Delete if empty. -->

