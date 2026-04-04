# Claude Code Instructions

See `.github/copilot-instructions.md` for all project conventions, code style, data layer patterns, i18n rules, and agent configuration.

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

## Key Paths

<!-- FILL: Add your project's key directories here -->

- Source code: `src/`
- Shared components: `_TBD_`
- API types: `_TBD_`
- Translations: `_TBD_`

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
