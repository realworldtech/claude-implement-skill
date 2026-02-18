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
| `/implement config` | View or update preferences (e.g., TDD mode) |

**Note**: `[name]` is optional - if you have multiple trackers, you can specify which one (e.g., `/implement status billing-spec`).

---

## Pre-Task Checklist

Before starting any task:

- [ ] Read the task description for section references (e.g., §4.2)
- [ ] Open and read those sections from the spec
- [ ] Note any specific formats, constraints, or edge cases mentioned
- [ ] Check the tracker for related completed work
- [ ] Check the tracker's `**TDD Mode**:` field to determine the workflow

### If TDD Mode is ON:

- [ ] Write tests first from the spec (sub-agent sees spec only, no implementation)
- [ ] Run tests — confirm they fail (validates tests check something real)
- [ ] Implement to make failing tests pass (sub-agent receives test file path)
- [ ] Run tests — confirm all pass (new + existing)
- [ ] If a test seems wrong: flag for user review, don't silently change it
- [ ] After tests pass, continue with the Post-Task Checklist below (linting, tracker update, etc.)

---

## Post-Task Checklist

After a sub-agent completes any task — **do not re-review the code manually**. Use objective checks:

- [ ] **Note the summary** from the sub-agent report — do NOT deeply re-analyse the output
- [ ] **Check DIGEST** (if sonnet sub-agent): extract `=== DIGEST ===`, check against complexity categories, dispatch opus review if matched
- [ ] **Run tests** for the changed code (pytest, npm test, etc.)
- [ ] **Fix any test failures** before marking complete
- [ ] **Run linting/type checks** if configured (mypy, flake8, eslint, tsc)
- [ ] **Spec compliance check** (recommended for non-trivial tasks): dispatch `prompts/spec-compliance-check.md` — replaces manual review
- [ ] **Commit** (if in a git repo): atomic commit for this task's changes — makes rollback easier
- [ ] Update tracker: change status, add file:line reference
- [ ] Add Implementation Log entry
- [ ] Note any gaps or ambiguities discovered
- [ ] Update task status with TaskUpdate

**Only dig deeper if**: tests fail, sub-agent flagged concerns, DIGEST triggered escalation, or compliance check found issues.

**Never mark a task complete if tests are failing.**

---

## Verification Checklist

During verification:

**FIRST - Validate code works:**
- [ ] **Run full test suite** - fix any failures before proceeding
- [ ] **Run linting/type checking** - fix any errors
- [ ] **Verify code compiles/runs** - no import errors, syntax errors

**THEN - Extract individual requirements:**
- [ ] Read spec structure (NOT full content) in main context
- [ ] Extract individual MUST/SHOULD/COULD requirements (not section headings)
- [ ] Build flat list: §N.M — one-line summary — impl hint from tracker
- [ ] A section with 15 subsections should produce 30-60+ requirements, NOT 15

**THEN - Verify at requirement level (parallel sub-agents):**
- [ ] Pre-flight: `mkdir -p <impl-dir>/.impl-verification/<name>/fragments/ && rm -f <impl-dir>/.impl-verification/<name>/fragments/*.done`
- [ ] ONE requirement = ONE sub-agent (hard rule)
- [ ] Each agent writes JSON fragment + `.done` marker to `<impl-dir>/.impl-verification/<name>/fragments/`
- [ ] Use `run_in_background: true` — do NOT read TaskOutput
- [ ] Check for previous verify reports — triggers re-verification mode if found

**THEN - Assemble report (deterministic):**
- [ ] Wait: `"$PYTHON" "$TOOLS_DIR/wait_for_done.py" --dir <impl-dir>/.impl-verification/<name>/fragments/ --count <N>`
- [ ] Assemble: `"$PYTHON" "$TOOLS_DIR/verify_report.py" --fragments-dir ... --output ...`
- [ ] Read the `.md` output to present summary to user
- [ ] For re-verification: add `--previous` flag pointing to previous report JSON

**Never claim verification is complete if tests are failing.**

---

## Fixing Verification Failures

**Always use Opus** when fixing gaps found during verification.

For each V-item gap:
1. Spawn a fix sub-agent with `model: "opus"`
2. Include: V-item ID, spec quote, current code, what's missing
3. After fix, re-verify that specific requirement (single sub-agent)
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

### Sub-Agent Output Pattern

All sub-agents write structured output to disk and respond with just "Done."

**Implementation/test/fix agents** write to: `<impl-dir>/.impl-work/<spec-name>/summary.json`
**Compliance check agents** write to: `<impl-dir>/.impl-work/<spec-name>/compliance.json`
**Verification agents** write to: `<impl-dir>/.impl-verification/<spec-name>/fragments/<id>.json`
**Fix-verification agents** write to: `<impl-dir>/.impl-work/<spec-name>/fix-summary.json`

All use `.done` markers to signal completion.

See the prompt templates in `prompts/` for the exact JSON formats.

### After Sub-Agent Returns

1. **Read the structured summary from disk** — NOT the agent's conversational output
2. Check for `concerns` or non-`complete` status in the summary
3. **Run tests** for affected code
4. Fix any test failures (use Opus for complex fixes)
5. Run linting/type checks
6. Only then update tracker as complete

```
# Example: read summary then run tests
Read("<impl-dir>/.impl-work/<spec-name>/summary.json")
Bash("pytest tests/test_affected_module.py -v")
```

---

## Large Spec Handling

When the spec has breakout section files (e.g., from `/spec`):

1. **Detect**: Look for `<!-- EXPANDED:` markers or `sections/` directory
2. **Build structural index**: `wc -c path/to/sections/*.md` → `estimated_tokens ≈ bytes / 4`
   - Sub-split files (`02a-`, `02b-`, `02c-`) are discovered by the same glob — group them under their parent section number
3. **Read only headings + requirement IDs** into main context (not full section prose)
4. **Pass file paths to sub-agents** — they read section files themselves
5. **Route by section size**: <5k tokens → sonnet (group 2-3), 5k-20k → sonnet (1 each), >20k → opus (1 each)
   - Sub-split sections route independently by own size; tasks referencing the parent section include all sub-file paths
6. **Digest-based escalation**: Sonnet agents produce a `=== DIGEST ===` at end of response. Check DIGEST against complexity categories (algorithms, state machines, permission/auth, complex business rules, cross-cutting). If matched → **mandatory** opus review of sonnet's changes

**Single-file specs**: Read the full file as normal — no structural index needed.

---

## Session Start Ritual

When starting or resuming work:

1. **Check for compaction**: If you feel uncertain about the implementation context, you may have experienced compaction
2. Run `/implement list` to see active implementations
3. Read the appropriate `.impl-tracker-<spec-name>.md`
4. **Worktree validation**: If the tracker's `**Worktree**` field is not `none`, verify the worktree path still exists and is on the expected branch. Set it as the implementation directory for all subsequent operations.
5. **Spec freshness check**: Compare current spec files against the stored Structural Index (multi-file) or baseline date (single-file). Look for new/removed files, >20% size changes, or new sub-split patterns. If changes detected, present user with options: re-scan affected sections, proceed as-is, or full re-plan.
6. **STRUCT check**: Look for `.spec-tracker-*.md` with `## Pending Structural Changes` — warn user if found
7. **Read the Recovery Instructions** section in the tracker if you're unsure of the workflow
8. Run `TaskList` to see pending tasks
9. Pick the next task
10. Read the spec sections for that task
11. Delegate to sub-agent for implementation

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
- [ ] **Tracker updated**: Requirements matrix reflects final state with file:line references
- [ ] **Gaps documented**: Any remaining gaps are documented with severity and rationale

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
