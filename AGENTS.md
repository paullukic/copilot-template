# Agent Context

<!--
  Quick summary for AI agents (Cursor, Windsurf, etc.).
  Full conventions: .github/copilot-instructions.md
-->

When working on this codebase:

- **Rules**: Follow `.github/copilot-instructions.md`.
- **Stack**: <!-- FILL: e.g. "Next.js 16, React 19, TypeScript, TanStack Query" -->
- **Structure**: <!-- FILL: e.g. "src/app/ pages, src/components/ shared, src/lib/ utilities" -->
- **Communication**: Direct, evidence-based, severity-rated. Every finding cites `file:line` with verbatim quotes. See `.github/copilot-instructions.md` § Communication Style.
- **Workflow**: Plan → Propose (OpenSpec) → Apply → Quality Gates → Review Gate → Done. Skip for trivial fixes. After 3 failed attempts, stop and ask.

If `.github/copilot-instructions.md` has unfilled sections (`FILL` or `_TBD_`), ask the user before coding.

### Agents

| Agent | Purpose |
|-------|---------|
| `@Reviewer` | Read-only code review |
| `@Debugger` | Root-cause analysis, minimal fixes |
| `@Planner` | Interview-driven planning |
| `@Verifier` | Evidence-based completion checks |
| `@Explore` | Codebase search and Q&A |

No separate `@Implementer` — the agent that plans also implements.
