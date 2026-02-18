# Fix Issue Prompt

Use this template when a sub-agent's implementation has gaps or errors that need fixing. **Always use Opus** for fix sub-agents.

```
Task(
  subagent_type: "general-purpose",
  model: "opus",
  prompt: "Fix implementation issue in [file].

  ## Problem
  [Describe the gap or error]

  ## Spec Requirement (§X.Y)
  [Quote the spec]

  ## Current Implementation
  [What exists now at file:line]

  ## Expected Fix
  [What needs to change]

  ## Before You Begin

  If anything is unclear about the problem or the expected fix — ask.
  Read the current code and the spec carefully before making changes.
  Don't assume the problem description is complete — verify it yourself.

  Summarize what you changed and confirm the fix addresses the spec requirement."
)
```

## When to Use

- Sub-agent's implementation doesn't match the spec
- Tests are failing after implementation
- DIGEST escalation flagged complexity issues
- Verification identified gaps (see also `fix-verification-gap.md` for V-item specific fixes)

## After the Fix

1. Re-run tests to confirm the fix works
2. Check for regressions in existing tests
3. Update the tracker with new implementation notes
