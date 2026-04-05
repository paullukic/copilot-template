# Agent Context

<!--
  This file provides a quick summary for AI agents (works with Cursor, Windsurf, etc.).
  The full conventions are in .github/copilot-instructions.md — that is the single source of truth.
-->

When working on this codebase:

- **Rules**: Follow the conventions in `.github/copilot-instructions.md`.
- **Stack**: <!-- FILL: Brief one-liner, e.g. "Next.js 16, React 19, TypeScript, TanStack Query" -->
- **Where things live**: <!-- FILL: Brief structure summary -->
- **Quality**: Use the project logger (no console.log), toast/notifications for user feedback, and follow code style rules.
- **Communication**: All agents use a direct, evidence-based, no-sugar-coating style. Every finding cites `file:line` with verbatim quotes and severity ratings. Audits end with a scorecard. See the Communication Style section in `.github/copilot-instructions.md`.
- **Workflow**: Before any non-trivial implementation, follow Plan → Propose (OpenSpec) → Apply → Quality Gates → Review Gate → Done. Skip planning when review output already exists in conversation. Skip the entire workflow for trivial single-file fixes. After 3 failed attempts, stop and ask.

If `.github/copilot-instructions.md` has unfilled sections (marked `FILL` or `_TBD_`), ask the user to provide the missing info before coding.

### Agents

| Agent | Purpose |
|-------|---------|
| `@Reviewer` | Read-only code reviewer checking conventions, specs, and bugs |
| `@Debugger` | Root-cause analysis and minimal fixes for bugs and build errors |
| `@Planner` | Interview-driven planning with codebase investigation |
| `@Verifier` | Evidence-based completion checks — runs tests, validates acceptance criteria |
| `@Explore` | Fast read-only codebase search and Q&A — prefer over manual search chains |

There is no separate `@Implementer` agent. The agent that plans and proposes also implements directly.

For detailed conventions, see `.github/copilot-instructions.md`.
