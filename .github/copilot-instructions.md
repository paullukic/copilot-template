# Copilot Instructions

- Always obey the rules in `AGENTS.md`.
- If `AGENTS.md` has unfilled sections (marked `FILL` or `_TBD_`), ask the user to provide the missing info before coding.
- Before coding:
  - If there is an active OpenSpec change in `openspec/changes/*/`, read its `proposal.md`, `specs/`, and `tasks.md`.
  - Implement code according to `tasks.md`, not ad hoc.
- When I paste a ticket, help me:
  - Turn it into an OpenSpec change (requirements, scenarios, tasks).
  - Then implement the tasks in small, reviewed steps.

## Review Role

When I ask you to review changes:

- Act as a strict reviewer, not an author.
- Use `AGENTS.md` and the relevant spec/change as the checklist.
- For each file:
  - Check if the implementation matches the spec tasks and requirements.
  - Flag missing tests or edge cases.
  - Highlight violations of architecture, naming, or i18n rules.
- Prefer concise, actionable comments over big rewrites.
