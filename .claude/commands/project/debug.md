Diagnose the following bug or build error. Find the root cause with minimal investigation, then apply the smallest possible fix.

Steps:
1. Read `.github/copilot-instructions.md` for project conventions.
2. Reproduce or understand the error from the description below.
3. Trace the root cause — grep for related patterns, read the relevant files.
4. Propose the minimal fix. Do not refactor unrelated code.
5. After fixing, run quality gates to verify.

Rules:
- Cite every finding with file:line.
- Fix only what's broken — no drive-by improvements.
- If the fix touches shared code, grep for all usages and verify no regressions.

$ARGUMENTS
