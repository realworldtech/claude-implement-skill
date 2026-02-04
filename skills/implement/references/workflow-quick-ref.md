# Implementation Workflow Quick Reference

## The Golden Rule

**Before touching any code, re-read the relevant spec section(s).**

This single habit prevents most implementation drift.

---

## Command Summary

| Command | When to Use |
|---------|-------------|
| `/implement spec.md` | Starting a new implementation |
| `/implement status [name]` | Checking progress mid-session |
| `/implement verify [name]` | After completing work, before delivery |
| `/implement continue [name]` | Resuming after a break or new session |
| `/implement list` | See all active implementations |

**Note**: `[name]` is optional - if you have multiple trackers, you can specify which one (e.g., `/implement status billing-spec`).

---

## Pre-Task Checklist

Before starting any task:

- [ ] Read the task description for section references (e.g., §4.2)
- [ ] Open and read those sections from the spec
- [ ] Note any specific formats, constraints, or edge cases mentioned
- [ ] Check the tracker for related completed work

---

## Post-Task Checklist

After completing any task:

- [ ] **Run tests** for the changed code (pytest, npm test, etc.)
- [ ] **Fix any test failures** before marking complete
- [ ] **Run linting/type checks** if configured (mypy, flake8, eslint, tsc)
- [ ] Update tracker: change status, add file:line reference
- [ ] Add Implementation Log entry
- [ ] Note any gaps or ambiguities discovered
- [ ] Update task status with TaskUpdate

**Never mark a task complete if tests are failing.**

---

## Verification Checklist

During verification:

**FIRST - Validate code works:**
- [ ] **Run full test suite** - fix any failures before proceeding
- [ ] **Run linting/type checking** - fix any errors
- [ ] **Verify code compiles/runs** - no import errors, syntax errors

**THEN - Verify spec compliance:**
- [ ] Re-read the ENTIRE spec (not just remembered parts)
- [ ] Walk through section by section
- [ ] For each requirement: find the code, confirm it matches
- [ ] Document gaps with specific section references
- [ ] Categorize gaps by severity (High/Medium/Low)

**Never claim verification is complete if tests are failing.**

---

## Fixing Verification Failures

**Always use Opus** when fixing gaps found during verification.

For each gap:
1. Spawn a fix sub-agent with `model: "opus"`
2. Include: spec quote, current code, what's missing
3. After fix, re-verify that specific section
4. Update tracker with new implementation notes
5. Repeat until all gaps resolved

Quick template:
```
Task(
  subagent_type: "general-purpose",
  model: "opus",
  prompt: "Fix gap in [file] for §X.Y.
  Spec says: [quote]
  Current: [file:line]
  Missing: [gap description]"
)
```

---

## Status Indicators

Use consistent status terms:

| Status | Meaning | Next Action |
|--------|---------|-------------|
| `pending` | Not started | Pick up when ready |
| `in_progress` | Currently working | Continue |
| `partial` | Some work done, gaps remain | Document gaps, continue |
| `complete` | Fully implemented | Verify during verification phase |
| `blocked` | Cannot proceed | Resolve blocker, then continue |
| `n/a` | Not applicable | Document why |

---

## Gap Documentation Template

When you find a gap:

```markdown
### GAP-XXX: <Short description> (§N.M)
- **Severity**: High | Medium | Low
- **Spec says**: "<exact quote>"
- **Current state**: <what exists now>
- **Missing**: <what's not there>
- **Suggested fix**: <how to address>
```

---

## Sub-Agent Workflow

### When to Delegate vs Work Inline

**Delegate to sub-agent:**
- Implementing discrete requirements (1-3 section references)
- Tasks with clear inputs (spec sections) and outputs (code changes)
- When main conversation context is getting large

**Keep in main conversation:**
- Planning and orchestration
- Reading/updating the tracker
- User interactions and decisions
- Final verification review

### Model Selection Guide

| Task Complexity | Model | Examples |
|-----------------|-------|----------|
| Straightforward | `haiku` or `sonnet` | Adding a field, simple CRUD, boilerplate |
| Moderate/Complex | `opus` | Logic decisions, algorithms, state management |
| Verification | `opus` | Always - catches subtle gaps |
| Fixing issues | `opus` | Always - requires understanding root cause |

**When in doubt, use `opus`**. If the task involves any logic decisions, conditional behavior, or algorithmic work, use `opus`.

### Sub-Agent Prompt Structure

```
Task(
  subagent_type: "general-purpose",
  model: "sonnet",
  prompt: "Implement [requirement] per §X.Y.

  ## Spec Requirement (§X.Y)
  [Exact quoted text from spec]

  ## Files to Modify
  - path/to/file.py

  ## Expected Changes
  - [What should be implemented]

  Summarize changes made and any issues encountered."
)
```

### After Sub-Agent Returns

1. **Run tests** for affected code
2. Fix any test failures (use Opus for complex fixes)
3. Run linting/type checks
4. Only then update tracker as complete

```
# Example test run after implementation
Bash("pytest tests/test_affected_module.py -v")
```

---

## Session Start Ritual

When starting or resuming work:

1. **Check for compaction**: If you feel uncertain about the implementation context, you may have experienced compaction
2. Run `/implement list` to see active implementations
3. Read the appropriate `.impl-tracker-<spec-name>.md`
4. **Read the Recovery Instructions** section in the tracker if you're unsure of the workflow
5. Run `TaskList` to see pending tasks
6. Pick the next task
7. Read the spec sections for that task
8. Delegate to sub-agent for implementation

### Recognizing Compaction

Signs you may have experienced compaction:
- Vague sense of "implementing something" without specifics
- Don't remember which spec sections you were working on
- Conversation feels like it's starting fresh mid-task

If this happens: Read the tracker first. It contains self-recovery instructions.

---

## Session End Ritual

Before ending a session:

1. Update tracker with current state
2. Add Implementation Log entry summarizing work done
3. Note any open questions or blockers
4. Commit changes if appropriate

---

## Definition of Done

Implementation is ONLY complete when ALL of these are true:

- [ ] **Tests pass**: All tests in the suite pass
- [ ] **No lint/type errors**: Code passes all configured checks
- [ ] **Code runs**: Application starts/compiles without errors
- [ ] **Spec verification complete**: All requirements implemented or documented as N/A
- [ ] **Tracker updated**: Requirements matrix reflects final state

**If no test suite exists**, at minimum:
- Import/load main modules to check for syntax errors
- Run any available linting tools
- Manually verify critical paths work

---

## Red Flags

Stop and re-read the spec if you notice:

- Implementing something not mentioned in spec
- Making assumptions about behavior
- Saying "I think" instead of "the spec says"
- Skipping a requirement because it seems hard
- Combining multiple features into one

**Stop and run tests if you notice:**

- About to mark a task as "complete" without running tests
- Sub-agent returned but you haven't validated the code works
- About to tell the user "implementation is done"
- Made changes to multiple files without testing
- Using field names or method names without verifying they exist

---

## Quick Tracker Update

Minimal tracker update after a task:

```markdown
| §X.Y | <requirement> | complete | src/module.py:123 |
```

Full log entry:

```markdown
### YYYY-MM-DD - <Task Summary>
- Implemented §X.Y: <brief description>
- Files changed: src/module.py, tests/test_module.py
- Notes: <any observations>
```
