Review the changes in scope for prop drilling, data flow problems, DRY violations, pattern consistency, dead code, hook misuse, component architecture, and type safety.

Be exhaustive — grep for patterns, count occurrences, cite every finding with file:line and verbatim code quotes. Use severity levels: Critical / Warning / Nit.

End with a scorecard: letter grade per category, aggregated metrics, and ranked fix priorities.

Rules:
- Read `.github/copilot-instructions.md` for project conventions.
- Every claim needs a specific file:line reference. No vague hand-waving.
- Don't find one instance and stop — count how widespread each problem is.
- If code is genuinely clean, say so in one line and move on.
- Do NOT edit any files. This is a read-only review.

$ARGUMENTS
