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

  ## Output — Write summary to disk

  Write your summary to: <impl-dir>/.impl-work/<spec-name>/summary.json

  {
    \"task\": \"fix §X.Y — [brief problem description]\",
    \"status\": \"complete\",
    \"files_changed\": [\"path/to/file.py\"],
    \"fix_description\": \"What was changed and why\",
    \"concerns\": []
  }

  After writing the JSON, write a completion marker:
  <impl-dir>/.impl-work/<spec-name>/summary.done (contents: just \"done\").
  The .done marker MUST be the last file you write.

  Then respond with just: Done."
)
```

## Pre-flight

Before dispatching, clear any previous markers:

```bash
rm -f <impl-dir>/.impl-work/<spec-name>/summary.done
```

## When to Use

- Sub-agent's implementation doesn't match the spec
- Tests are failing after implementation
- DIGEST escalation flagged complexity issues
- Verification identified gaps (see also `fix-verification-gap.md` for V-item specific fixes)

## After the Fix

1. Read `<impl-dir>/.impl-work/<spec-name>/summary.json` for the fix summary
2. Re-run tests to confirm the fix works
3. Check for regressions in existing tests
4. Update the tracker with new implementation notes
5. Do NOT re-analyse the agent's conversational output
