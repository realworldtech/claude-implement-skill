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

## Plan-Execute Loop

Each master task (from Phase 1) goes through a **plan-execute cycle**. The planning phase breaks the master task into visible sub-tasks and gets user approval; the execution phase runs each sub-task using the TDD test-first pattern.

**This loop should already be described in the plan's `## Execution Protocol` section** (written during Phase 1). If the plan doesn't have one, add it now before proceeding — see `references/phase-1-planning.md` Step 5 for the template. The Execution Protocol ensures the loop survives context compaction.

### Critical Loop Rules

These rules are non-negotiable:

1. **ONE GROUP AT A TIME.** Only plan and execute the next pending master task. Do NOT create plans that cover multiple groups or "plan Groups 2-5." Each group gets its own planning session.
2. **WORKTREE DISCIPLINE.** If the tracker has a worktree path, ALL file edits, test runs, and sub-agent dispatches target that worktree — not the main tree. Check `git rev-parse --show-toplevel` before any file operation if unsure.
3. **RETURN TO PLANNING AFTER EACH GROUP.** When a master task is complete (all sub-tasks done, tests pass, tracker updated), the next action is `EnterPlanMode` for the next pending master task. Do NOT proceed directly to execution.

### Master Task Planning Phase

For the **next pending master task only** (not multiple tasks):

1. **`EnterPlanMode`**
2. Read the tracker file to get section references
3. **Re-read the relevant section(s) from the original spec document** (for single-file specs) or **confirm which section file(s) the sub-agent will need to read** (for multi-file specs)
4. Explore the codebase — identify files that need modification, existing patterns, test conventions, test file locations
5. Assess scope: how many files, what complexity?
6. **Break into sub-tasks** — create visible sub-tasks via `TaskCreate` with specific subjects (e.g., "Add PrintRequest model with status field"). Each sub-task should be small enough for a single TDD cycle (write tests → implement → pass).
7. **Write a plan** — the plan **MUST** begin with the skill context preamble:

   > **Skill context** — This plan is part of the **/implement skill** executing
   > Group N (`<master-task-subject>`) of `<spec-name>`.
   > TDD mode: `on`. Tracker: `<tracker-path>`.
   > Workflow ref: `skills/implement/references/phase-2-tdd.md`.
   > [If worktree: Worktree: `<path>` (branch: `<branch>`).]
   >
   > **After context clear**: Re-read the tracker at `<tracker-path>` and
   > `skills/implement/references/phase-2-tdd.md` to restore
   > orchestration context before continuing execution.
   >
   > **On group completion**: Update tracker → mark master task complete →
   > STOP → call `EnterPlanMode` for the next pending group.
   > Do NOT continue to the next group without a new planning cycle.

   After the preamble, the plan covers:
   - Implementation approach
   - Sub-task breakdown with files and test strategy per sub-task
   - Which test files to create, which spec sections the test-writing agent will receive
   - Dependencies between sub-tasks
8. **`ExitPlanMode`** — scope `allowedPrompts` to the Bash operations needed (e.g., test commands, build commands)
9. **Create a checkpoint task** — after creating all implementation sub-tasks, create one final sub-task: "Complete Group N: update tracker and return to planning". This task is a structural reminder — when you reach it, follow its instructions literally.

If the user rejects the plan, re-enter plan mode with an adjusted approach. If the user says to skip or do something else, follow their direction.

### Sub-Task Execution Phase

For each sub-task, go through a lightweight plan-execute cycle:

1. **`EnterPlanMode`** — confirm the approach still applies given the current codebase state. Identify any adjustments needed (e.g., earlier sub-tasks may have added models that change the test strategy).
2. **`ExitPlanMode`** — user approves the refined approach
3. Execute using the TDD test-first cycle below. **If in a worktree**, ensure sub-agent prompts include the worktree path as the working directory for all file operations.
4. After execution, update tracker and mark the sub-task complete.
5. When all sub-tasks are done, mark the master task complete.

**After marking the master task complete:** Do NOT continue to the next master task's execution. Instead, call `EnterPlanMode` to plan the next pending master task. This is the loop — each group gets its own planning session with user approval.

If new sub-tasks are discovered during execution, create them via `TaskCreate` before proceeding.

### Anti-Rationalization Rules

| Thought | Why it's wrong |
|---------|---------------|
| "I know what the next group needs, I'll just continue" | Each group needs its own planning cycle. The plan for Group N+1 depends on what Group N actually produced. |
| "The tracker update can wait until I finish the next group" | Compaction between groups loses all progress. Update at every boundary. |
| "This is a simple group, I don't need to plan it" | Every group gets planned. No exceptions for simplicity. |
| "I'll just do the sub-tasks without the plan-execute loop" | The loop exists because sub-agents need user-approved scope. Skipping it leads to drift. |

### Step 1: Write Tests First

**Pre-flight**: Clear previous markers:

```bash
mkdir -p <impl-dir>/.impl-work/<spec-name>/ && rm -f <impl-dir>/.impl-work/<spec-name>/summary.done
```

Delegate test writing using the prompt template at `prompts/tdd-write-tests.md`. The sub-agent works **purely from the spec** — it should NOT see any implementation code.

After the agent completes, read `<impl-dir>/.impl-work/<spec-name>/summary.json` for the test summary. Do NOT re-analyse conversational output.

### Step 3: Run Tests — Confirm Failures

Run the test suite. The new tests **should fail** (since implementation doesn't exist yet). This validates:
- Tests are checking something real (not trivially passing)
- Tests are syntactically valid and runnable
- Test infrastructure works

**If tests pass unexpectedly**: Investigate — either the feature already exists, or tests are too loose.

**If tests error (import/syntax)**: Fix the test setup (imports, fixtures, file paths), not the test assertions themselves.

### Step 4: Implement to Pass Tests

Clear previous markers, then delegate implementation using the prompt template at `prompts/tdd-implement.md`:

```bash
rm -f <impl-dir>/.impl-work/<spec-name>/summary.done
```

Key difference from standard workflow: the implementation agent receives the test file path as acceptance criteria.

### Step 5: Validate (Main Conversation)

After the implementation sub-agent completes (TaskOutput returns "Done."), **read the structured summary from disk** — do NOT re-analyse conversational output:

1. **Read the summary**: `<impl-dir>/.impl-work/<spec-name>/summary.json`
   - Check `concerns` — if non-empty, investigate
   - Check `status` — if not `complete`, investigate
2. **Check DIGEST for complexity escalation** (sonnet agents only):
   - Read the `digest` field from `summary.json`
   - Check signals against the complexity category table in `references/sub-agent-strategy.md`
   - If any category matches: dispatch opus to review the sonnet's code changes
3. **Run the full test suite**:
   - **New tests should now pass** — confirms implementation meets the spec
   - **Existing tests should still pass** — no regressions
   - If new tests still fail: fix the implementation (not the tests), then re-run
   - If a test seems genuinely wrong: **flag it for user review** rather than changing the test
   - If existing tests break: fix the regression in the implementation
4. **Spec compliance check** (optional but recommended for non-trivial tasks):
   - Use `prompts/spec-compliance-check.md` — feed it the spec text and `files_changed` from `summary.json`
   - Read the verdict from `<impl-dir>/.impl-work/<spec-name>/compliance.json`

**Only dig deeper if**: tests fail, `concerns` is non-empty, DIGEST triggered escalation, or the compliance check found issues.

### Step 6: Commit (If in a Git Repo)

If the project is a git repository, create an atomic commit for this task's changes. This makes it easier to review, revert, or cherry-pick individual tasks.

- Stage only the files changed by this task (tests + implementation)
- Use a descriptive commit message referencing the section: e.g., `feat: implement merge detection (§2.4)`
- If not in a git repo, skip this step

### Step 7: Update Tracker

Same as the standard workflow's Step 6 — see `references/phase-2-implementation.md`.

**Only mark as `complete` after both new and existing tests pass.**

## Handling Issues in TDD Mode

If the implementation sub-agent cannot make all tests pass:

1. Review the failing tests against the spec to confirm they're correct
2. If tests are correct: use `prompts/fix-issue.md` with both spec text and failing test output
3. If a test misinterprets the spec: flag it for user review before changing it
4. Never silently modify tests to match a wrong implementation
