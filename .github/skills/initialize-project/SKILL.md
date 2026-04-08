---
name: initialize-project
description: Initialize a new project with the copilot template. Interactive setup that auto-detects the tech stack and fills in all template placeholders.
argument-hint: Target project path (optional — will ask if not provided).
license: MIT
metadata:
  author: copilot-template
  version: "1.0"
---

Initialize a new project with this copilot template. Auto-detect the tech stack from the target repo and fill in all template placeholders.

---

## Step 1: Gather Info

Ask the user these questions using the **vscode_askQuestions tool** (wait for answers before proceeding):

1. **Target project path** — "What is the full path to the project you want to initialize?" (If provided as argument, use that.)
2. **Which AI tools should I set up for?**
   - Claude Code (`CLAUDE.md`, `.claude/commands/`)
   - VS Code Copilot (`.github/copilot-instructions.md`, `.github/agents/`, `.github/skills/`, `.github/prompts/`)
   - Both (recommended default)
3. **Any sections to skip entirely?** (e.g., i18n, API design, data layer) — optional, user can say "none"
4. **Any additional project-specific coding/review rules?**
  - Ask for concise bullets (for example: mandatory architecture patterns, domain invariants, naming restrictions, module boundaries, logging/security constraints).

## Step 2: Detect Tech Stack

Investigate the TARGET project to auto-detect as much as possible. Read these files if they exist:

- `README.md` — project description, setup instructions, architecture
- `package.json` — Node.js deps, scripts
- `tsconfig.json` / `jsconfig.json` — TypeScript/JS config
- `Cargo.toml` — Rust
- `go.mod` — Go
- `pyproject.toml`, `setup.py`, `requirements.txt` — Python
- `pom.xml`, `build.gradle` — Java/Kotlin
- `Gemfile` — Ruby
- `.eslintrc*`, `.prettierrc*`, `biome.json` — linter/formatter
- `docker-compose.yml`, `Dockerfile` — infrastructure hints
- `Makefile` — build commands
- `src/` directory listing — project structure

Extract:
- **Language** (TypeScript, Python, Rust, Go, Java, etc.)
- **Framework** (React, Next.js, FastAPI, Axum, Spring Boot, etc.)
- **ORM / Data layer** (Prisma, Drizzle, SQLAlchemy, GORM, etc.)
- **Testing** (Jest, Vitest, pytest, go test, JUnit, etc.)
- **Build tool** (Vite, Webpack, esbuild, Cargo, Maven, etc.)
- **Linter/Formatter** (ESLint, Prettier, Biome, Ruff, rustfmt, etc.)
- **Commands** (dev, build, lint, test, format, typecheck)
- **Project structure** (key directories and purpose)
- **i18n** (mechanism if any)
- **API style** (REST, GraphQL, tRPC, etc.)

Present findings in a summary table and ask the user to confirm or correct before proceeding.

## Step 3: Copy Template Files

Copy files from the copilot-template repo to the target project. Only copy what's relevant to the tools selected in Step 1.

**For VS Code Copilot:**
- `.github/copilot-instructions.md`
- `.github/agents/` (all agent `.md` files)
- `.github/skills/` (all skill directories including `initialize-project/` — the target project can use it to initialize other projects later)
- `.github/prompts/` (all prompt `.md` files)
- `.github/instructions/` (all instruction `.md` files)
- `AGENTS.md`

**For Claude Code:**
- `CLAUDE.md`
- `.claude/commands/project/` (all command files EXCEPT `initialize.md`)

**For both:** all of the above.

**Always copy:**
- `openspec/config.yaml` (create `openspec/` dir if needed)

**Do NOT overwrite** existing files without asking. If a file exists, show both versions side by side (existing vs template) and ask the user how to proceed:
- **Overwrite** — replace entirely with the template version
- **Skip** — keep the existing file unchanged
- **Section-by-section** — show each differing section and let the user choose which version to keep for each one

Do NOT attempt automatic merging — the risk of duplicated or corrupted content is too high.

## Step 4: Fill In Placeholders

Using the detected info from Step 2, replace all `_TBD_` placeholders and `<!-- FILL: ... -->` comment blocks in the copied files.

**In `.github/copilot-instructions.md`:**
- Stack table — fill with detected technologies
- Commands table — fill with detected scripts/commands
- Project Structure table — fill with detected paths and purposes
- Code Style sections — fill based on language/framework conventions
- Naming Conventions — fill based on language idioms
- Data Layer, Testing, API Design, i18n, Errors and Logging — fill or delete as appropriate
- Remove `<!-- FILL: ... -->` comments after filling
- Delete sections the user said to skip
- Add user-provided project-specific rules under `## Project-Specific Rules` (create concise bullet points; do not duplicate existing global rules)

**In `CLAUDE.md`:**
- Quick Reference commands table
- Key Paths based on detected structure
- Keep workflow, critical rules, and delegation sections as-is (universal)

**In `AGENTS.md`:**
- Stack one-liner
- Structure summary

## Step 5: Verify

1. Grep target project instruction files for remaining `_TBD_` or `<!-- FILL` markers
2. If any remain, ask the user for the missing info and continue filling until the grep returns zero matches
3. Grep copied agent/skill files for deprecated tool aliases (`AskUserQuestion`, `TodoWrite`, `replace_string_in_file`, `multi_replace_string_in_file`) and replace with runtime-supported names where needed
4. Show a summary of all files created/modified
5. Ask if the user wants to commit the changes

## Guardrails

- Never guess at commands — if you can't detect them, ask.
- Never invent project structure — read the actual filesystem.
- If the target already has `CLAUDE.md` or `copilot-instructions.md`, warn and ask (merge/overwrite/skip).
- Keep the communication style, implementation workflow, and review role sections intact — those are template features.
- Prefer what the project already does over generic defaults.
- Initialization is complete only when there are zero `_TBD_` and `<!-- FILL` markers in copied instruction files.
