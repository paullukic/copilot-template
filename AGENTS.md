# Project Conventions

<!--
  HOW TO USE THIS TEMPLATE:
  1. Fill in every section marked with FILL.
  2. Delete sections that don't apply to your project.
  3. Add project-specific rules as needed.
  4. If you ask Copilot to "set up AGENTS.md" or "read the README",
     it will find unfilled sections and ask you for the missing info.
-->

## Mindset

- No bias toward user preferences -- follow project conventions and best practices.
- No assumptions -- ask for context when unclear.
- Match existing codebase patterns exactly.
- Prioritize simplicity and maintainability.
- Do not leave residue code after changes.

---

## Tech Stack

<!-- FILL: Replace _TBD_ with your actual stack. Delete rows that don't apply. -->

| Component | Technology |
|-----------|------------|
| Language | _TBD_ |
| Framework | _TBD_ |
| ORM / Data layer | _TBD_ |
| Testing | _TBD_ |
| Build tool | _TBD_ |
| API specs | _TBD_ |
| Migration tool | _TBD_ |

---

## Language & Style Rules

<!-- FILL: Add language-specific rules for your stack. Keep what applies, delete the rest, add your own. -->

### General
- Use immutable locals where possible.
- Compare enums safely (`.equals()` in Java, `===` in TypeScript, `is` in Python).
- Prefer constructor/dependency injection over field injection.
- No hardcoded strings for user-facing content (use i18n).
- No business logic in controllers/handlers.
- Always add documentation on service-layer methods.
- Throw project-standard exceptions for business errors -- do not create ad-hoc exception classes.

### Validation
- Do not duplicate validations already enforced by the API spec or schema.
- Only add business-logic validations that the spec cannot express.

### Avoid unnecessary abstractions
- Do not introduce intermediate types just to shuttle data between two methods in the same class.

<!-- FILL: Add language-specific rules. Examples:
  Java: val/var conventions, Lombok annotations, MapStruct usage
  TypeScript: strict mode, prefer interfaces over types, barrel exports
  Python: type hints, dataclasses vs pydantic, async patterns
-->

---

## Database Migrations

<!-- FILL: Customize for your migration tool. Delete this section if not applicable. -->

- Changeset author: <!-- FILL: your-name -->, never `copilot`.
- Prefer declarative migration syntax over raw SQL when available.
- Schema changes to a table must also be applied to its audit counterpart (if applicable).
- Timestamps should use timezone-aware types.

---

## Naming Conventions

<!-- FILL: Adjust patterns for your language/framework. -->

| Kind | Pattern |
|------|---------|
| Controller / Handler | `*Controller` |
| Service | `*Service` |
| Repository / DAO | `*Repository` |
| Unit test | `*Test` |
| Integration test | `*TestIT` or `*IntegrationTest` |

---

## Testing

<!-- FILL: Adjust for your testing framework and patterns. -->

- Use setup methods (e.g. `@BeforeEach`, `setUp()`, `beforeEach()`) for test initialization.
- Use mocking frameworks for isolating dependencies.
- Integration tests live alongside unit tests in the same package.
- Package by feature, not layer.
- Cover edge cases: nulls, empty collections, boundary values.

---

## API Design

<!-- FILL: Adjust for your API style. Delete if not building APIs. -->

- REST endpoints under `/api/v1/`.
- HTTP status codes: 200, 201, 204, 400, 404, 500.
- UUIDs for resource IDs.
- Endpoints defined in API specs generate interfaces/types -- never hand-write what codegen produces.

---

## Module / Package Structure

<!-- FILL: Map your actual project structure. -->

| Module / Directory | Purpose |
|--------------------|---------|
| _TBD_ | _TBD_ |

---

## Related Repositories

<!-- FILL: List other repos this project depends on or shares code with. Delete if single-repo. -->
<!-- The Reviewer agent uses this list to check cross-repo impact. -->

| Repository | Path (local) | Relationship |
|------------|-------------|---------------|
| _TBD_ | _TBD_ | _TBD_ |

---

## Security

<!-- FILL: Add project-specific security rules. Delete rules that don't apply, add your own. -->

- Never log secrets, tokens, or passwords -- even at DEBUG level.
- Validate and sanitize all external input at system boundaries.
- Use parameterized queries -- never concatenate user input into SQL/HQL.
- Authentication and authorization checks happen in the framework layer, not in business logic.
- Secrets come from environment variables or a vault -- never hardcoded.

---

## Internationalization (i18n)

<!-- FILL: Describe how i18n works in this project. Delete if not applicable. -->

- Mechanism: <!-- FILL: e.g. message bundles, i18next, gettext, react-intl -->
- All user-facing strings must go through the i18n mechanism.
- Key naming convention: <!-- FILL: e.g. dot-separated: module.feature.label -->
- No hardcoded user-facing text in code.

---

## Project-Specific Rules

<!-- FILL: Add any rules unique to this project that don't fit above. Delete if empty. -->


