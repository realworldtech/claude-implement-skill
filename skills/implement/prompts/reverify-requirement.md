# Re-Verification Prompt

Use this template when re-verifying a previously identified V-item. **Always use Opus.** **Always run in background.**

For each **open** V-item (status was Partial/Not Implemented, or test coverage was Partial/None), spawn a sub-agent with the original finding AND the spec requirement.

```
Task(
  subagent_type: "general-purpose",
  model: "opus",
  run_in_background: true,
  prompt: """Re-verify a previously identified issue.

## Previous Finding

V12 — §3.2 — AI Thumbnail Generation
**Previous status**: Partial
**Previous issue**: Uses full URL instead of relative path for thumbnail src
**Previous implementation**: templates/library/book_detail.html:45

## Spec Requirement

<paste the spec requirement text>

## CRITICAL: Verify Independently — Do Not Assume Fixed

The previous finding may have been addressed, partially addressed, or not addressed
at all. Do NOT assume progress was made — verify by reading the actual code.

- A "fix" commit may not actually fix the issue
- The file/line references may have shifted
- New code may introduce different problems while claiming to fix the original

## Instructions

1. Read the implementation file(s) referenced in the previous finding
2. Check if the specific issue has actually been addressed — read the code, don't trust commit messages
3. Search for the current implementation if the file/line has changed
4. Re-assess test coverage for this requirement
5. If the issue appears fixed, verify it's fully fixed — not just partially patched

## Output — Write findings to disk as JSON

Write your findings to: .impl-verification/<spec-name>/fragments/03-02.json

Use this EXACT JSON format:
{
  "schema_version": "1.0.0",
  "fragment_id": "03-02",
  "section_ref": "§3.2",
  "title": "AI Thumbnail Generation",
  "requirement_text": "<the spec requirement text>",
  "moscow": "MUST",
  "status": "implemented",
  "v_item_id": "V12",
  "previous_status": "partial",
  "resolution": "fixed",
  "implementation": {
    "files": [{"path": "file.py", "lines": "123", "description": "current implementation"}],
    "notes": ""
  },
  "test_coverage": "full",
  "tests": [{"path": "test_file.py", "lines": "45", "description": "what's tested"}],
  "missing_tests": [],
  "missing_implementation": [],
  "notes": "Describe what changed or why it's still open"
}

Valid resolution values: fixed, partially_fixed, not_fixed, regressed

After writing the JSON, write a completion marker:
.impl-verification/<spec-name>/fragments/03-02.done (contents: just "done").
"""
)
```

## For Passed V-Items (Spot-Check)

For V-items that previously passed (Implemented + Full test coverage), do a **lightweight spot-check**: cluster 5-10 passed items into a single sub-agent that confirms the implementations still exist and haven't regressed. This is a sanity check, not a deep re-audit.
