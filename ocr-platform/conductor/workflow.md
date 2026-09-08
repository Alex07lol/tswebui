# Workflow — OCR Platform

## TDD Policy

**Moderate** — tests are required for all service/business logic and provider implementations. UI stub pages don't require tests. Tests must be written alongside (or before) implementation, not after.

## Commit Strategy

**Conventional Commits:**

```
feat:     New feature or capability
fix:      Bug fix
chore:    Build setup, config, dependencies
test:     Test additions or corrections
refactor: Code improvement without behaviour change
docs:     Documentation only
```

Each task completion produces at least one commit. Format:

```
feat: <task description> (<trackId>)
```

## Code Review

Optional / self-review OK for now (single-developer project). All phase completions must pass automated tests before proceeding.

## Verification Checkpoints

**After each phase completion:**

1. Run full automated test suite (`pytest -v`).
2. Manually verify the phase success criteria from the spec.
3. Commit the updated `plan.md` with all tasks marked `[x]`.
4. Only then proceed to the next phase.

## Task Lifecycle

```
[ ] Not started
[~] In progress
[x] Complete
```

## Implementation Order Principle

From `instructions.md` §53:

> Do not build pattern learning before the extraction configuration model is stable.
> Pattern learning should generate configurations.
> Therefore the configuration model is the foundation.

Build phases strictly in order: 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7.
