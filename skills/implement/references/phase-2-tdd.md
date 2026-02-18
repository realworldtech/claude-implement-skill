# Phase 2 (TDD Mode): Test-First Implementation

This workflow runs **instead of** the standard Phase 2 when TDD mode is active (tracker shows `**TDD Mode**: on`). The key difference: tests are written first from the spec before any implementation exists, then implementation is done to make them pass.

## Why TDD Mode Works Well with Sub-Agents

- **Spec fidelity**: The test-writing agent reads only the spec — no implementation code exists to bias it
- **Clear acceptance criteria**: The implementation agent has concrete pass/fail signals from the tests
- **Drift detection**: If the implementation agent can't make tests pass, it reveals misunderstandings early
- **Different contexts catch different things**: Test and implementation agents interpret the spec independently
- **Regression safety**: Tests exist before code, so there's no "forgot to write tests" problem

## Pre-Implementation Check

Same as the standard workflow — verify the tracker exists with a populated Requirements Matrix and tasks have been created. See `references/phase-2-implementation.md` for the checklist.

## TDD Implementation via Sub-Agents

For each task, follow this test-first cycle:

### Step 1: Prepare Context (Main Conversation)

Same as the standard workflow:

1. Read the tracker file to get the section references
2. **Re-read the relevant section(s) from the original spec document** (for single-file specs) or **confirm which section file(s) the sub-agent will need to read** (for multi-file specs)
3. Note any specific requirements, formats, or constraints mentioned
4. Identify relevant existing code files and test conventions

### Step 2: Write Tests First

Delegate test writing using the prompt template at `prompts/tdd-write-tests.md`. The sub-agent works **purely from the spec** — it should NOT see any implementation code.

### Step 3: Run Tests — Confirm Failures

Run the test suite. The new tests **should fail** (since implementation doesn't exist yet). This validates:
- Tests are checking something real (not trivially passing)
- Tests are syntactically valid and runnable
- Test infrastructure works

**If tests pass unexpectedly**: Investigate — either the feature already exists, or tests are too loose.

**If tests error (import/syntax)**: Fix the test setup (imports, fixtures, file paths), not the test assertions themselves.

### Step 4: Implement to Pass Tests

Delegate implementation using the prompt template at `prompts/tdd-implement.md`. Key difference from standard workflow: the implementation agent receives the test file path as acceptance criteria.

### Step 5a: Check DIGEST for Complexity Escalation

After the implementation sub-agent completes and before running tests:

1. Extract the `=== DIGEST ===` section from the sub-agent's response
2. Check DIGEST signals against the complexity category table in `references/sub-agent-strategy.md`
3. If any category matches: dispatch opus to review the sonnet's code changes
4. Run tests after any opus-driven changes

This step only applies when the implementation sub-agent was a sonnet. Skip for opus agents.

### Step 5: Run Tests — Confirm Passes

Run the full test suite:
- **New tests should now pass** — confirms implementation meets the spec
- **Existing tests should still pass** — no regressions
- If new tests still fail: fix the implementation (not the tests), then re-run
- If a test seems genuinely wrong: **flag it for user review** rather than changing the test
- If existing tests break: fix the regression in the implementation

### Step 6: Update Tracker

Same as the standard workflow's Step 5 — see `references/phase-2-implementation.md`.

**Only mark as `complete` after both new and existing tests pass.**

## Handling Issues in TDD Mode

If the implementation sub-agent cannot make all tests pass:

1. Review the failing tests against the spec to confirm they're correct
2. If tests are correct: use `prompts/fix-issue.md` with both spec text and failing test output
3. If a test misinterprets the spec: flag it for user review before changing it
4. Never silently modify tests to match a wrong implementation
