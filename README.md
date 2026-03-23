# Copilot Template

Reusable VS Code Copilot customization files for any project.

## For Copilot: Bootstrap Instructions

When a user adds this template to a new project and asks you to set it up:

1. **Read `AGENTS.md`** and find all sections marked with `<!-- FILL: ... -->`.
2. **Ask the user** for the missing information. Group your questions:
   - Tech stack (language, framework, ORM, build tool, test framework)
   - Naming conventions (if different from defaults)
   - Module/package structure
   - Database migration tool and author name
   - Any project-specific rules
3. **Fill in the sections** with the answers. Remove the `<!-- FILL: ... -->` comments.
4. **Delete sections** the user says don't apply (e.g., no DB migrations, no API specs).
5. **Confirm** the final `AGENTS.md` with the user.

If the user says "read the README" or "set up my project", this is what they mean.

## Structure

```
AGENTS.md                              # Project conventions (customize per repo)
.github/
  copilot-instructions.md              # Repo-scoped instructions (auto-discovered)
  agents/
    reviewer.agent.md                  # Strict code reviewer agent
  skills/
    openspec-apply-change/
      SKILL.md                         # Implement tasks with auto-review gate
```

## Setup

Copy into a new project:

```bash
cp AGENTS.md /path/to/your-project/
cp -r .github/ /path/to/your-project/.github/
```

Then ask Copilot: "Read the README and set up AGENTS.md for this project."

## What's Included

### AGENTS.md (template)
Project conventions checklist with `<!-- FILL -->` markers. Copilot reads this file before every task and enforces its rules. Sections: tech stack, language rules, naming, testing, API design, migrations, module structure.

### Reviewer Agent (`@Reviewer`)
Read-only code reviewer that checks against:
- Project conventions (AGENTS.md)
- Spec/task compliance (OpenSpec or similar)
- Deep bug hunting (NPEs, control flow, concurrency, data integrity)
- Simplicity and cleanliness
- Cross-module impact

### Apply-Change Skill (OpenSpec)
Implements tasks from OpenSpec changes with a built-in workflow:
1. Read spec context
2. Implement tasks one by one
3. **Auto-review** -- invokes Reviewer agent before build verification
4. If issues found: adds fix tasks, implements, re-reviews
5. Build verification

Requires [openspec CLI](https://github.com/openspec-dev/openspec). Delete this skill if you don't use OpenSpec.

## Example Bootstrap Conversation

```
User: Read the README and set up AGENTS.md for this project.

Copilot: I found unfilled sections in AGENTS.md. I need some info:

1. Tech stack:
   - Language & version? (e.g., Java 17, TypeScript 5, Python 3.12)
   - Framework? (e.g., Spring Boot, Next.js, FastAPI)
   - ORM/data layer? (e.g., JPA/Hibernate, Prisma, SQLAlchemy)
   - Test framework? (e.g., JUnit 5 + Mockito, Jest, pytest)
   - Build tool? (e.g., Maven, Gradle, npm, Poetry)

2. Do you use API specs (OpenAPI, GraphQL schema)?
3. Do you use database migrations? If so, which tool (Liquibase, Flyway, Alembic, Prisma Migrate)?
4. Do you have related repositories that share contracts/APIs?
5. How does i18n work? (message bundles, i18next, gettext, or N/A)
6. Any project-specific rules I should know?

User: Java 17, Spring Boot, JPA, JUnit 5, Maven. We use OpenAPI specs.
       Liquibase for migrations, author name "john". No related repos.
       i18n via Spring MessageSource, keys like module.feature.label.
       No extra rules.

Copilot: Done! I've filled in AGENTS.md and removed sections that don't
         apply (Related Repositories). Want me to review the result?
```

## Auto-Discovery

| File | Discovered by | Purpose |
|------|---------------|---------|
| `AGENTS.md` | VS Code Copilot (repo root) | Project conventions |
| `.github/copilot-instructions.md` | VS Code Copilot | Workflow instructions |
| `.github/agents/*.agent.md` | VS Code Copilot | Custom agents (`@AgentName`) |
| `.github/skills/*/SKILL.md` | VS Code Copilot | Invokable skills |
