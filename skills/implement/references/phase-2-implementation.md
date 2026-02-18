# Phase 2: Standard Implementation

**Workflow selection**: Check the tracker's `**TDD Mode**:` field. If `on` or not set, use `references/phase-2-tdd.md` instead. If `off`, use this workflow. If the field is missing, check preferences to determine the mode and update the tracker — default is `on`.

## Pre-Implementation Check

**Before writing any implementation code**, verify:
1. A tracker file (`.impl-tracker-*.md`) exists in the implementation directory (worktree or current directory)
2. The tracker has a populated Requirements Matrix
3. Tasks have been created via TaskCreate

If any of these are missing, STOP and complete Phase 1 first.

## Implementation via Sub-Agents

For each task, use the sub-agent delegation pattern to preserve main conversation context. Read `references/sub-agent-strategy.md` for model selection and routing details.

### Step 1: Prepare Context (Main Conversation)

**CRITICAL**: Before delegating any task:

1. Read the tracker file to get the section references
2. **Re-read the relevant section(s) from the original spec document** (for single-file specs) or **confirm which section file(s) the sub-agent will need to read** (for multi-file specs)
3. Note any specific requirements, formats, or constraints mentioned
4. Identify relevant existing code files the sub-agent will need

This prevents drift by ensuring you're always working from the source of truth.

### Step 2: Delegate to Sub-Agent

Spawn a sub-agent for the implementation work. The prompt style depends on spec type:

- **Single-file specs**: Use the prompt template at `prompts/implement-single-file.md`
- **Multi-file specs**: Use the prompt template at `prompts/implement-multi-file.md`

### Step 3: Review and Verify (Main Conversation)

After the implementation sub-agent completes:

1. Review the changes made by the sub-agent
2. Verify they match the spec requirements
3. **Run existing tests** to check for regressions:
   - Run the full test suite or at minimum the relevant test files
   - If tests fail, fix the issues before proceeding
4. If issues found:
   - For minor fixes: fix directly
   - For complex issues: use `prompts/fix-issue.md` to spawn an Opus fix agent
   - **Re-run tests after any fix**
5. **Check DIGEST for complexity escalation** (multi-file/sonnet agents only):
   - Extract the `=== DIGEST ===` section from the sub-agent's response
   - Check DIGEST signals against the complexity category table in `references/sub-agent-strategy.md`
   - If any category matches: dispatch opus to review the sonnet's code changes
   - Run tests again after any opus-driven changes

### Step 3a: Spec Compliance Check (Optional)

After tests pass, optionally run a lightweight spec compliance check using the prompt template at `prompts/spec-compliance-check.md`. This catches implementation drift early rather than waiting for Phase 3.

**Recommended for**: tasks involving multiple requirements, complex logic, or sonnet-implemented work. **Skip for**: trivially simple tasks or when Phase 3 verification is imminent.

### Step 4: Write Tests for New Functionality

After the implementation is reviewed and existing tests pass, delegate test writing using the prompt template at `prompts/write-tests.md`.

After the test sub-agent completes, **run the full test suite** to confirm both new and existing tests pass.

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
