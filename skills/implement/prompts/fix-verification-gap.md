# Fix Verification Gap Prompt

Use this template when fixing gaps identified during verification. **Always use Opus** for fixes — verification failures often involve subtle misunderstandings of requirements or edge cases.

```
Task(
  subagent_type: "general-purpose",
  model: "opus",  // Always Opus for fixes
  prompt: "Fix verification gap identified as V<N>.

  ## V-Item Details
  - **V-item**: V<N> — §X.Y — <requirement title>
  - **Spec requirement**: [exact quote]
  - **Current state**: [what exists at file:line]
  - **What's missing**: [from verification report]

  ## Working Directory
  Work in: <implementation_dir>

  ## Task
  1. Read the current implementation
  2. Understand why it doesn't meet the spec
  3. Implement the fix to fully satisfy §X.Y
  4. Summarize what you changed"
)
```

## After Each Fix

1. Re-verify that specific requirement (single sub-agent, same pattern as `verify-requirement.md`)
2. Run tests to confirm the fix works and no regressions
3. Update the tracker with new implementation notes
4. Repeat until all gaps are resolved

Never claim verification is complete until tests pass.
