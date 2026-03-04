# Phase 2: Standard Implementation

**Workflow selection**: Check the tracker's `**TDD Mode**:` field. If `on` or not set, use `references/phase-2-tdd.md` instead. If `off`, use this workflow. If the field is missing, check preferences to determine the mode and update the tracker — default is `on`.

## Pre-Implementation Check

**Before writing any implementation code**, verify:
1. A tracker file (`.impl-tracker-*.md`) exists in the implementation directory (worktree or current directory)
2. The tracker has a populated Requirements Matrix
3. Tasks have been created via TaskCreate

If any of these are missing, STOP and complete Phase 1 first.

## Plan-Execute Loop

Each master task (from Phase 1) goes through a **plan-execute cycle**. The planning phase breaks the master task into visible sub-tasks and gets user approval; the execution phase runs each sub-task individually.

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
4. Explore the codebase — identify files that need modification, existing patterns, test conventions
5. Assess scope: how many files, what complexity?
6. **Break into sub-tasks** — create visible sub-tasks via `TaskCreate` with specific subjects (e.g., "Add PrintClient model to models.py"). Each sub-task should be small enough to execute in a single sub-agent dispatch.
7. **Write a plan** — the plan **MUST** begin with the skill context preamble:

   > **Skill context** — This plan is part of the **/implement skill** executing
   > Group N (`<master-task-subject>`) of `<spec-name>`.
   > TDD mode: `off`. Tracker: `<tracker-path>`.
   > Workflow ref: `skills/implement/references/phase-2-implementation.md`.
   > [If worktree: Worktree: `<path>` (branch: `<branch>`).]
   >
   > **After context clear**: Re-read the tracker at `<tracker-path>` and
   > `skills/implement/references/phase-2-implementation.md` to restore
   > orchestration context before continuing execution.
   >
   > **On group completion**: Update tracker → mark master task complete →
   > STOP → call `EnterPlanMode` for the next pending group.
   > Do NOT continue to the next group without a new planning cycle.

   After the preamble, the plan covers:
   - Implementation approach
   - Sub-task breakdown with files and test strategy per sub-task
   - Dependencies between sub-tasks
8. **`ExitPlanMode`** — scope `allowedPrompts` to the Bash operations needed (e.g., test commands, build commands)
9. **Create a checkpoint task** — after creating all implementation sub-tasks, create one final sub-task: "Complete Group N: update tracker and return to planning". This task is a structural reminder — when you reach it, follow its instructions literally.

If the user rejects the plan, re-enter plan mode with an adjusted approach. If the user says to skip or do something else, follow their direction.

### Sub-Task Execution Phase

For each sub-task, go through a lightweight plan-execute cycle:

1. **`EnterPlanMode`** — confirm the approach still applies given the current codebase state (earlier sub-tasks may have changed things). Identify any adjustments needed.
2. **`ExitPlanMode`** — user approves the refined approach
3. Execute using sub-agents (see below). Read `references/sub-agent-strategy.md` for model selection and routing details. **If in a worktree**, ensure sub-agent prompts include the worktree path as the working directory for all file operations.
4. After execution, update tracker and mark the sub-task complete.
5. When all sub-tasks are done, mark the master task complete.

**After marking the master task complete:** Do NOT continue to the next master task's execution. Instead, call `EnterPlanMode` to plan the next pending master task. This is the loop — each group gets its own planning session with user approval.

If new sub-tasks are discovered during execution (e.g., an unexpected dependency), create them via `TaskCreate` before proceeding.

### Anti-Rationalization Rules

| Thought | Why it's wrong |
|---------|---------------|
| "I know what the next group needs, I'll just continue" | Each group needs its own planning cycle. The plan for Group N+1 depends on what Group N actually produced. |
| "The tracker update can wait until I finish the next group" | Compaction between groups loses all progress. Update at every boundary. |
| "This is a simple group, I don't need to plan it" | Every group gets planned. No exceptions for simplicity. |
| "I'll just do the sub-tasks without the plan-execute loop" | The loop exists because sub-agents need user-approved scope. Skipping it leads to drift. |

### Step 1: Delegate to Sub-Agent

**Pre-flight**: Clear previous markers before dispatching:

```bash
mkdir -p <impl-dir>/.impl-work/<spec-name>/ && rm -f <impl-dir>/.impl-work/<spec-name>/summary.done
```

Spawn a sub-agent for the implementation work. The prompt style depends on spec type:

- **Single-file specs**: Use the prompt template at `prompts/implement-single-file.md`
- **Multi-file specs**: Use the prompt template at `prompts/implement-multi-file.md`

### Step 3: Validate (Main Conversation)

After the sub-agent completes (TaskOutput returns "Done."), **read the structured summary from disk** — do NOT re-analyse the agent's conversational output:

1. **Read the summary**: `<impl-dir>/.impl-work/<spec-name>/summary.json`
   - Check `concerns` — if non-empty, investigate
   - Check `status` — if not `complete`, investigate
2. **Check DIGEST for complexity escalation** (multi-file/sonnet agents only):
   - Read the `digest` field from `summary.json`
   - Check signals against the complexity category table in `references/sub-agent-strategy.md`
   - If any category matches: dispatch opus to review the sonnet's code changes
3. **Run tests** to check for regressions:
   - Run the full test suite or at minimum the relevant test files
   - If tests fail: use `prompts/fix-issue.md` to spawn an Opus fix agent, then re-run tests
4. **Spec compliance check** (optional but recommended for non-trivial tasks):
   - Use `prompts/spec-compliance-check.md` — feed it the spec text and the `files_changed` from `summary.json`
   - Read the verdict from `<impl-dir>/.impl-work/<spec-name>/compliance.json`
   - This replaces manual review — an independent agent with fresh context is more reliable

**Only dig deeper if**: tests fail, `concerns` is non-empty, DIGEST triggered escalation, or the compliance check found issues.

### Step 4: Write Tests for New Functionality

Clear previous markers, then delegate test writing using the prompt template at `prompts/write-tests.md`:

```bash
rm -f <impl-dir>/.impl-work/<spec-name>/summary.done
```

After the test sub-agent completes, read `summary.json` for the test list, then **run the full test suite** to confirm both new and existing tests pass.

### Step 5: Commit (If in a Git Repo)

If the project is a git repository, create an atomic commit for this task's changes. This makes it easier to review, revert, or cherry-pick individual tasks.

- Stage only the files changed by this task (implementation + tests)
- Use a descriptive commit message referencing the section: e.g., `feat: implement merge detection (§2.4)`
- If not in a git repo, skip this step

### Step 6: Update Tracker

**Only update to `complete` after implementation is verified AND tests pass.**

1. Update the tracker file:
   - Change status from `pending` to `complete` or `partial`
   - Add implementation notes with file:line references
   - Add test file references (required — not optional)
   - Add entry to Implementation Log

2. Update the task status using TaskUpdate

Example tracker update:
```markdown
| §2.4 | Detect merged tickets | complete | EdgeCaseHandler.check_merge() at src/handlers.py:156 | test_handlers.py:45 |
```

**Do not mark as `complete` if:**
- Tests are failing
- You haven't run the tests
- New functionality has no tests
- There are linting/type errors

## Handling Sub-Agent Issues

If a sub-agent's implementation has gaps or errors, use the prompt template at `prompts/fix-issue.md` to spawn an Opus fix agent.
