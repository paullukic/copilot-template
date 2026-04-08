---
name: openspec-propose
description: Propose a new change with all artifacts generated in one step. Use when the user wants to quickly describe what they want to build and get a complete proposal with design, specs, and tasks ready for implementation.
argument-hint: Change name or description (e.g., "add user settings page").
license: MIT
compatibility: Requires openspec CLI.
metadata:
  author: openspec
  version: "1.0"
  generatedBy: "1.2.0"
---

Propose a new change - create the change and generate all artifacts in one step.

I'll create a change with artifacts:
- proposal.md (what & why, goals/non-goals, decisions, impact, risks — single document, no separate design.md)
- specs/<capability>/spec.md (requirements with BDD scenarios)
- tasks.md (implementation steps — grouped by logical unit, not per-file)

When ready to implement, run /opsx:apply

---

**Input**: The user's request should include a change name (kebab-case) OR a description of what they want to build.

**Steps**

1. **If no clear input provided, ask what they want to build**

   Use the **vscode_askQuestions tool** (open-ended, no preset options) to ask:
   > "What change do you want to work on? Describe what you want to build or fix."

   From their description, derive a kebab-case name (e.g., "add user authentication" → `add-user-auth`).

   **IMPORTANT**: Do NOT proceed without understanding what the user wants to build.

2. **Create the change directory**
   ```bash
   openspec new change "<name>"
   ```
   **If the command fails**: report the error verbatim. Do NOT create the directory structure manually or invent artifact names. Ask the user to verify the CLI is installed and working.

   This creates a scaffolded change at `openspec/changes/<name>/` with `.openspec.yaml`.

3. **Get the artifact build order**
   ```bash
   openspec status --change "<name>" --json
   ```
   **If the command fails or returns invalid JSON**: report the error verbatim. Do NOT invent artifact IDs, dependency orders, or schema structures. Ask the user to check the CLI.

   Parse the JSON to get:
   - `applyRequires`: array of artifact IDs needed before implementation (e.g., `["tasks"]`)
   - `artifacts`: list of all artifacts with their status and dependencies

4. **Create artifacts in sequence until apply-ready**

   Use the **manage_todo_list tool** to track progress through the artifacts.

   Loop through artifacts in dependency order (artifacts with no pending dependencies first):

   a. **For each artifact that is `ready` (dependencies satisfied)**:
      - Get instructions:
        ```bash
        openspec instructions <artifact-id> --change "<name>" --json
        ```
      - The instructions JSON includes:
        - `context`: Project background (constraints for you - do NOT include in output)
        - `rules`: Artifact-specific rules (constraints for you - do NOT include in output)
        - `template`: The structure to use for your output file
        - `instruction`: Schema-specific guidance for this artifact type
        - `outputPath`: Where to write the artifact
        - `dependencies`: Completed artifacts to read for context
      - Read any completed dependency files for context
      - Create the artifact file using `template` as the structure
      - Apply `context` and `rules` as constraints - but do NOT copy them into the file
      - Show brief progress: "Created <artifact-id>"

   b. **Continue until all `applyRequires` artifacts are complete**
      - After creating each artifact, re-run `openspec status --change "<name>" --json`
      - Check if every artifact ID in `applyRequires` has `status: "done"` in the artifacts array
      - Stop when all `applyRequires` artifacts are done
      - **Safety limit**: If you have created more than 20 artifacts without reaching apply-ready state, STOP. Report the current status and ask the user — the schema may have a circular dependency or misconfiguration.

   c. **If an artifact requires user input** (unclear context):
      - Use **vscode_askQuestions tool** to clarify
      - Then continue with creation

5. **Show final status**
   ```bash
   openspec status --change "<name>"
   ```

**Output**

After completing all artifacts, summarize:
- Change name and location
- List of artifacts created with brief descriptions
- What's ready: "All artifacts created! Ready for implementation."
- Prompt: "Run `/opsx:apply` or ask me to implement to start working on the tasks."

**Artifact Creation Guidelines**

- Follow the `instruction` field from `openspec instructions` for each artifact type
- The schema defines what each artifact should contain - follow it
- Read dependency artifacts for context before creating new ones
- Use `template` as the structure for your output file - fill in its sections
- **IMPORTANT**: `context` and `rules` are constraints for YOU, not content for the file
  - Do NOT copy `<context>`, `<rules>`, `<project_context>` blocks into the artifact
  - These guide what you write, but should never appear in the output

**Guardrails**
- Create ALL artifacts needed for implementation (as defined by schema's `apply.requires`)
- Always read dependency artifacts before creating a new one
- If context is critically unclear, ask the user. Otherwise, make reasonable decisions to keep momentum — do not block on minor ambiguities
- If a change with that name already exists, ask if user wants to continue it or create a new one
- Verify each artifact file exists after writing before proceeding to next

## Common Rationalizations

These are excuses agents use to skip steps. Do not accept them.

| Rationalization | Reality |
|---|---|
| "The requirements are clear enough to skip the spec" | If they were, you wouldn't need an agent. Write the spec — it takes 5 minutes and prevents 2 hours of rework. |
| "I'll figure out the details during implementation" | That's how features get half-built and re-scrapped. Surface unknowns in the proposal, not in code. |
| "This is too small for a proposal" | If it touches 3+ files or changes behavior, it needs a proposal. Small proposals are fine. |
| "The user seems impatient, I'll just start coding" | Starting without a contract means rework when assumptions are wrong. A 2-minute proposal saves a 30-minute redo. |
| "I know the codebase well enough to skip investigation" | You don't know what changed since your last context. Read the relevant files before proposing. |

## Red Flags

- Proposal created without reading any existing source code.
- Tasks that are per-file ("update file X", "update file Y") instead of per-logical-unit.
- Missing Risks section or empty Non-Goals.
- More than 10 tasks — scope is too large, split the change.
- Proposal proceeding to implementation without explicit user approval.
- Impact section that doesn't list specific file paths.

## Verification

After generating the proposal, confirm:

- [ ] `proposal.md` has all required sections (Why, Goals, Non-Goals, Decisions, Impact, Risks).
- [ ] `tasks.md` has 3-7 tasks (max 10), grouped by logical unit.
- [ ] Every task has a clear description and files list.
- [ ] The Impact section lists specific file paths, not vague module names.
- [ ] Risks section is honest — not empty or minimized.
- [ ] The user was explicitly asked for approval before any implementation.
