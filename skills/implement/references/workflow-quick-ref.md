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

- [ ] Update tracker: change status, add file:line reference
- [ ] Add Implementation Log entry
- [ ] Note any gaps or ambiguities discovered
- [ ] Update task status with TaskUpdate

---

## Verification Checklist

During verification:

- [ ] Re-read the ENTIRE spec (not just remembered parts)
- [ ] Walk through section by section
- [ ] For each requirement: find the code, confirm it matches
- [ ] Document gaps with specific section references
- [ ] Categorize gaps by severity (High/Medium/Low)

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

## Session Start Ritual

When starting or resuming work:

1. Run `/implement list` to see active implementations
2. Read the appropriate `.impl-tracker-<spec-name>.md`
3. Run `TaskList` to see pending tasks
4. Pick the next task
5. Read the spec sections for that task
6. Begin implementation

---

## Session End Ritual

Before ending a session:

1. Update tracker with current state
2. Add Implementation Log entry summarizing work done
3. Note any open questions or blockers
4. Commit changes if appropriate

---

## Red Flags

Stop and re-read the spec if you notice:

- Implementing something not mentioned in spec
- Making assumptions about behavior
- Saying "I think" instead of "the spec says"
- Skipping a requirement because it seems hard
- Combining multiple features into one

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
