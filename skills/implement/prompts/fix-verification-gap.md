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

  ## Output — Write summary to disk

  Write your summary to: <implementation_dir>/.impl-work/<spec-name>/fix-summary.json

  {
    \"v_item\": \"V<N>\",
    \"section_ref\": \"§X.Y\",
    \"status\": \"complete\",
    \"files_changed\": [\"path/to/file.py\"],
    \"fix_description\": \"What was changed and why\",
    \"concerns\": []
  }

  After writing the JSON, write a completion marker:
  <implementation_dir>/.impl-work/<spec-name>/fix-summary.done (contents: just \"done\").
  The .done marker MUST be the last file you write.

  Then respond with just: Done."
)
```

## Pre-flight

Before dispatching, clear any previous markers:

```bash
rm -f <implementation_dir>/.impl-work/<spec-name>/fix-summary.done
```

## After Each Fix

1. Read `<implementation_dir>/.impl-work/<spec-name>/fix-summary.json` for the fix summary
2. Re-verify that specific requirement (single sub-agent, background, same pattern as `verify-requirement.md`)
3. Run tests to confirm the fix works and no regressions
4. Update the tracker with new implementation notes
5. Repeat until all gaps are resolved
6. Do NOT re-analyse the agent's conversational output

Never claim verification is complete until tests pass.
