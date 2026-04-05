Review the changes in scope for data flow problems, DRY violations, pattern consistency, dead code, architectural issues, and type safety.

Be exhaustive — grep for patterns, count occurrences, cite every finding with file:line and verbatim code quotes. Use severity levels: Critical / Warning / Nit.

End with a scorecard: letter grade per category, aggregated metrics, and ranked fix priorities.

## Change Manifest (mandatory pre-step)

Before running the review checklist, build a change manifest. This is the primary review input — NOT raw diffs.

1. Run `git diff origin/main --stat` to get the list of changed files.
2. For each changed file, run `git diff origin/main -- <file>` one file at a time.
3. For each file, write a 1-2 line summary of what changed. Focus on:
   - What was renamed, added, removed, or rewired
   - For fields set to `null`/`undefined`/hardcoded/default values: note the old source
   - For type/interface changes: note old type -> new type
   - For removed/added parameters, fields, or methods: note what was removed/added
4. Group changes by logical unit. Exclude auto-generated files (note them as "auto-generated, skip").
5. Use the manifest to drive the review — read actual files and trace impact, do NOT review raw diff hunks.

If the caller provides a manifest via $ARGUMENTS, use it directly and skip manifest generation.

## Rules

- Read `.github/copilot-instructions.md` for project conventions.
- Every claim needs a specific file:line reference. No vague hand-waving.
- Don't find one instance and stop — count how widespread each problem is.
- If code is genuinely clean, say so in one line and move on.
- Do NOT edit any files. This is a read-only review.
- For fields/parameters set to `null`/`undefined`/default: trace the full write path through to the API or persistence layer. Flag destructive clears or silent data loss.
- For type/interface renames: verify the new type has all members accessed by consumers.
- For condition/state changes: verify consistency between guard conditions and the data they protect.

$ARGUMENTS
