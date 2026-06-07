# Project Rules for Codex

## Core Working Rules

1. Break a project into multiple features. Work feature by feature, not by generating the entire project at once.
2. Before implementing a feature, clearly state:

   * Feature name
   * Goal
   * Files expected to change
   * Acceptance criteria
   * Tests or validation to run
3. Implement only the stated feature.
4. After implementation, summarize:

   * What changed
   * Why it was changed
   * How to run or test it
   * Any known limitations
5. Do not move to the next feature until the current feature is complete, documented, tested, and committed.
6. Keep user-facing answers crisp. Answer the question directly or explain what is being done with a simple example. Avoid unnecessary text unless the user asks for detailed explanation.
7. After completing each feature, provide a crisp summary with:

   * What was done
   * What files were changed
   * What commands were run
   * What output or result was produced
   * A simple example when helpful
8. Explanations should be short paragraphs by default, not long bullet-heavy responses, unless the topic needs more detail. Use a simple structure when useful:

   * Explanation
   * Files changed
   * Commands run
   * Outcome
   * What happened to the data
   * Next step
9. If the user says "shazam" in a request, answer crisply without examples.

## Agent Workflow

Use an internal agent-style workflow for every feature:

* Planner: breaks down the feature and identifies files to modify
* Engineer: implements the code
* Analytics/Data Engineer: validates data logic, SQL, transformations, and metrics
* QA Engineer: checks tests, edge cases, failures, and data-quality rules
* Documentation Engineer: updates docs and usage notes
* Reviewer: reviews the final diff before commit

Use GPT-5.5 Codex High reasoning mode if available.

## Feature Documentation Rules

Maintain a `docs/` folder.

For every feature, create or update a markdown file under:

```text
docs/features/
```

Each feature document must include:

* Feature name
* Goal
* Files changed
* Implementation details
* How to run it
* Tests or validation performed
* Known limitations
* Next steps

Do not leave features undocumented.

## README Update Rule

After every meaningful feature, update `README.md` only with information that is already implemented.

Do not describe unfinished functionality as complete.

The README should stay accurate at all times.

The README should be crisp telling what the feature is, what the feature accomplished and how it made the project better.

## Code Quality Rules

* Write clean, modular, production-quality code.
* Keep functions small and testable.
* Use clear names for files, functions, variables, tables, and columns.
* Use type hints where practical.
* Use logging instead of unnecessary print statements.
* Avoid hard-coded local paths.
* Use configuration files, environment variables, or constants where appropriate.
* Do not duplicate logic across files.
* Prefer simple, maintainable solutions over over-engineered ones.

## Data Rules

* Inspect real data before assuming schemas.
* Do not invent columns, metrics, datasets, or results.
* Do not fabricate performance claims, screenshots, or outputs.
* Keep raw data out of git unless it is a tiny sample specifically created for tests.
* Add `.gitignore` rules for large data files, generated files, local environments, credentials, and cache folders.
* Document all assumptions clearly.

## Testing and Validation Rules

Every feature should include relevant tests or validation.

Use at least one of the following when appropriate:

* Unit tests
* Data-quality checks
* SQL validation queries
* Row count checks
* Schema checks
* Null checks
* Duplicate checks
* Edge-case checks
* Manual validation instructions

If automated tests are not possible for a feature, explain why and provide manual validation steps.

## Commit Rules

Commit after each completed feature.

Use clear commit messages such as:

```text
feat: initialize project structure
feat: add data ingestion workflow
feat: implement data quality checks
feat: create analytics mart
feat: add dashboard views
docs: update architecture notes
test: add transformation tests
fix: handle missing timestamp values
```

Before every commit:

1. Review the changed files.
2. Run relevant tests or validation.
3. Update docs.
4. Update README if needed.
5. Commit only related changes.

Do not make one large final commit for the whole project.

## Git Rules

* Do not commit secrets, credentials, API keys, Kaggle tokens, `.env`, raw large datasets, or generated cache files.
* Keep commits focused and meaningful.
* If git commit is not available in the environment, provide the exact commands the user should run manually.

## Documentation Quality Rules

Documentation should be clear enough that another engineer can understand and run the project.

Maintain or create docs for:

* Architecture
* Data dictionary
* Validation rules
* Decision log
* Feature notes
* Setup instructions
* Known limitations

Do not leave major design decisions undocumented.

## Accuracy Rules

* Be truthful about what is implemented.
* Do not overstate the project.
* Do not claim production readiness unless the project actually has production-level setup.
* Do not claim cloud deployment unless it is actually deployed.
* Do not claim real-time capability unless the pipeline actually supports it.
* Mark unfinished work clearly as planned, ongoing, or future work.

## Final Review Rule

Before considering the project complete, perform a final review covering:

* Code structure
* Tests and validation
* README accuracy
* Feature documentation
* Data assumptions
* Reproducibility
* Resume alignment
* Known limitations
* Git commit history
