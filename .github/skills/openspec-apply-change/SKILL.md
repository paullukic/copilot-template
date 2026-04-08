---
name: openspec-apply-change
description: Implement tasks from an OpenSpec change. Use when the user wants to start implementing, continue implementation, or work through tasks.
argument-hint: Change name (e.g., "add-dark-mode"). If omitted, will prompt for selection.
license: MIT
compatibility: Requires openspec CLI.
metadata:
  author: openspec
  version: "1.0"
  generatedBy: "1.2.0"
---

Implement tasks from an OpenSpec change.

**Input**: Optionally specify a change name. If omitted, check if it can be inferred from conversation context. If vague or ambiguous you MUST prompt for available changes.

**Steps**

1. **Select the change**

   If a name is provided, use it. Otherwise:
   - Infer from conversation context if the user mentioned a change
   - Auto-select if only one active change exists
   - If ambiguous, run `openspec list --json` to get available changes and use the **vscode_askQuestions tool** to let the user select

   Always announce: "Using change: <name>" and how to override (e.g., `/opsx:apply <other>`).

2. **Check status to understand the schema**
   ```bash
   openspec status --change "<name>" --json
   ```
   **If the command fails or returns invalid JSON**: report the error verbatim to the user. Do NOT invent schema names, artifact names, or task structures. Ask the user to verify the change exists and the CLI is installed.

   Parse the JSON to understand:
   - `schemaName`: The workflow being used (e.g., "spec-driven")
   - Which artifact contains the tasks (typically "tasks" for spec-driven, check status for others)

3. **Get apply instructions**

   ```bash
   openspec instructions apply --change "<name>" --json
   ```
   **If the command fails or returns invalid JSON**: report the error verbatim. Do NOT guess at context file paths or task structures.

   This returns:
   - Context file paths (varies by schema - could be proposal/specs/design/tasks or spec/tests/implementation/docs)
   - Progress (total, complete, remaining)
   - Task list with status
   - Dynamic instruction based on current state

   **Handle states:**
   - If `state: "blocked"` (missing artifacts): show which artifacts are missing, then suggest the user run `/opsx:propose` to create them
   - If `state: "all_done"`: congratulate, suggest archive
   - Otherwise: proceed to implementation

4. **Read context files**

   For each file in `contextFiles`, run `read_file` to confirm it exists on disk.
   - **If a file is missing**: report which file and its expected path. PAUSE and ask the user for the correct location or whether to proceed without it. Do NOT confabulate file contents. **Recovery**: once the user provides a corrected path or says to proceed without it, continue from this step — do not restart the skill from the beginning.
   - **If all files exist**: read them for context.

   The files depend on the schema being used:
   - **spec-driven**: proposal, specs, tasks
   - Other schemas: follow the contextFiles from CLI output

5. **Show current progress**

   Display:
   - Schema being used
   - Progress: "N/M tasks complete"
   - Remaining tasks overview
   - Dynamic instruction from CLI

6. **Classify change size** (determines which steps to run)

   Count total lines changed across all tasks (estimate from task descriptions and file reads).
   - **Quick** (≤3 tasks AND ≤50 lines changed, no new files created): Run steps 7 → 9A → 10 → 11 (skip full self-verification gate and full auto-review).
   - **Standard** (everything else): Run all steps 7 → 12.

   Announce: "Change classified as **quick/standard** — [skipping/running] verification gates."

7. **Implement tasks (loop until done or blocked)**

   **CRITICAL**: The tasks.md is your work order — follow it literally. Never rewrite, reinterpret, or regenerate the tasks. Never invent field names, API types, or schemas that don't exist in the actual source code.

   For each pending task:
   - Show which task is being worked on
   - **Read all source files** you'll modify — in full — before making any changes
   - **Verify field/type names** exist in the actual codebase: run `grep_search` for each field/type name before using it. If a name cannot be found: STOP, report what's missing, and ask the user. Do NOT assume alternative names or invent types.
   - Make the code changes required using file editing tools (`apply_patch`, `create_file`, etc.)
   - Every task MUST result in actual file edits, not descriptions of what to do
   - Keep changes minimal and focused
   - **Before marking complete**: verify you made actual file changes for this task. If a task produced zero file edits, it is not complete — either implement it or ask the user if the task should be removed.
   - Mark task complete in the tasks file: `- [ ]` → `- [x]`
   - Continue to next task

   **Pause if:**
   - Task is unclear → ask for clarification
   - Implementation reveals a design issue → suggest updating artifacts
   - Error or blocker encountered → report and wait for guidance
   - User interrupts

8. **Self-verification gate** (standard changes only — skip for quick)

   Run these checks before invoking the Reviewer. Each check must produce concrete evidence.

   1. **Feature inventory** (always): For modified files, compare original (`git show HEAD:<path>`) with current version. For new files, verify against spec. List features: PRESERVED (with line) or REMOVED. Restore any feature removed without explicit spec request.
   2. **Spec text match** (always): Re-read the spec. Grep for every UI label/tooltip/helper text. Report: spec text → file:line. Flag mismatches.
   3. **i18n checks** (only if project uses i18n): Verify new/changed keys exist in all language files. Grep for orphaned keys and remove them.
   4. **API constraint check** (only if change involves form state → API flags): Read API type definitions, check for mutual exclusivity.

   Fix failures before proceeding.

9. **Auto-review** (standard changes only — skip for quick)

   - **VS Code**: Invoke `@Reviewer`. **Claude Code**: Run `/project:review`. Both produce equivalent output.
   - If **REQUEST_CHANGES**: add findings as tasks under "Review Fixes" (use "Round 2" heading if section already exists). Implement fixes, then re-invoke Reviewer on changed files only.
   - **Circuit breaker**: After 3 review cycles on the same code area, STOP and ask the user. Do NOT continue without explicit approval.
   - If **APPROVE**: proceed to build verification.

9A. **Lightweight review gate** (quick changes only)

   - Run a targeted review pass on changed files only (business logic correctness + code logic correctness).
   - If issues are found, fix them before build verification.
   - Keep this pass lightweight, but do not skip it.

10. **Build verification**

   Check `.github/copilot-instructions.md` for the project's build/quality commands. Run them in the documented order. If any command fails, fix the issue and re-run.

   If the build commands are not documented, ask the user.

11. **On completion or pause, show status**

   Display:
   - Tasks completed this session
   - Overall progress: "N/M tasks complete"
   - If all done: suggest archive
   - If paused: explain why and wait for guidance

**Output During Implementation**

```
## Implementing: <change-name> (schema: <schema-name>)

Working on task 3/7: <task description>
[...implementation happening...]
✓ Task complete

Working on task 4/7: <task description>
[...implementation happening...]
✓ Task complete
```

**Output On Completion**

```
## Implementation Complete

**Change:** <change-name>
**Schema:** <schema-name>
**Progress:** 7/7 tasks complete ✓

### Completed This Session
- [x] Task 1
- [x] Task 2
...

All tasks complete! Ready to archive this change.
```

**Output On Pause (Issue Encountered)**

```
## Implementation Paused

**Change:** <change-name>
**Schema:** <schema-name>
**Progress:** 4/7 tasks complete

### Issue Encountered
<description of the issue>

**Options:**
1. <option 1>
2. <option 2>
3. Other approach

What would you like to do?
```

**Guardrails**
- Keep going through tasks until done or blocked
- Always read context files before starting (from the apply instructions output)
- If task is ambiguous, pause and ask before implementing
- If implementation reveals issues, pause and suggest artifact updates
- Keep code changes minimal and scoped to each task
- Update task checkbox immediately after completing each task
- Pause on errors, blockers, or unclear requirements - don't guess
- Use contextFiles from CLI output, don't assume specific file names

## Common Rationalizations

These are excuses agents use to skip steps. Do not accept them.

| Rationalization | Reality |
|---|---|
| "I'll run tests at the end" | Bugs compound. A bug in Task 1 makes Tasks 2-5 wrong. Verify after each task. |
| "This task is too small to verify" | Small changes break builds. Run the quality gate — it takes seconds. |
| "The reviewer will catch it" | The reviewer is not your safety net. Self-verify before handing off. |
| "I'll clean up the dead code later" | Later never comes. Clean up residue imports and variables before marking a task done. |
| "These changes are related so I'll do them together" | Mixing concerns makes review harder and rollback impossible. One logical change per task. |
| "The spec is wrong, I'll fix it in code" | The spec is a contract. If it's wrong, pause and ask — don't silently deviate. |

## Red Flags

- More than 100 lines written without running tests or build.
- Tasks marked "done" with zero file edits.
- Skipping the self-verification gate because "changes are small."
- Multiple unrelated changes bundled into one task.
- Build or tests broken between tasks and not immediately fixed.
- Touching files outside the task scope "while I'm here."

## Verification

After completing all tasks, confirm:

- [ ] Every task in `tasks.md` produced actual file edits.
- [ ] All existing tests still pass.
- [ ] The build succeeds.
- [ ] No existing features were accidentally removed (feature inventory checked).
- [ ] Residue code cleaned up (dead imports, unused variables).
- [ ] The Reviewer has been invoked and returned a verdict.
- [ ] All Critical findings from review are resolved.

**Fluid Workflow Integration**

This skill supports the "actions on a change" model:

- **Can be invoked anytime**: Before all artifacts are done (if tasks exist), after partial implementation, interleaved with other actions
- **Allows artifact updates**: If implementation reveals design issues, suggest updating artifacts - not phase-locked, work fluidly
