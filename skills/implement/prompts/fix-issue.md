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
  [What needs to change]"
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
