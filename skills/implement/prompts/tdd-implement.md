# TDD Implementation Prompt

Use this template when implementing code to make failing TDD tests pass (TDD Mode, Phase 2 TDD Step 4). The key difference from the standard implementation prompt: include the test file path so the implementation agent knows the acceptance criteria.

**Model selection**: Use `sonnet` for straightforward tasks, `opus` for complex logic or algorithms.

**For multi-file specs**: Pass the section file path instead of quoting the full text.

```
Task(
  subagent_type: "general-purpose",
  model: "sonnet",  // Use "opus" for complex logic or algorithms
  prompt: "Implement §X.Y to make the failing tests pass.

  ## Spec Requirement (§X.Y)
  [Exact spec text — or for multi-file specs: 'Read the spec section at: path/to/sections/section-X.md']

  ## Failing Tests
  Tests at [test_file:lines] define the acceptance criteria.
  Read them to understand what's expected.

  ## Files to Modify
  - path/to/file.py (describe what changes needed)

  ## Context
  [Any relevant existing code patterns or constraints]

  ## Before You Begin

  If anything is unclear about the requirements, the test expectations, or
  constraints — ask. It's better to clarify now than to implement the wrong thing.

  ## While You Work

  If you encounter something unexpected or need to make a judgment call, ask rather
  than guess. Don't make assumptions about ambiguous requirements.

  ## Important
  - Make the failing tests pass
  - Don't modify the tests
  - Also ensure existing tests still pass

  ## Before Reporting Back: Self-Review

  Before you report, review your own work:

  **Completeness**: Did I implement everything needed to satisfy both the spec
  and the tests? Are there edge cases I missed?

  **Quality**: Are names clear and accurate? Is the code clean and maintainable?
  Does it follow existing patterns in the codebase?

  **Discipline**: Did I avoid overbuilding (YAGNI)? Did I only build what was
  needed to pass the tests and satisfy the spec?

  If you find issues during self-review, fix them before reporting.

  ## Output — Write summary to disk

  Write your summary to: <impl-dir>/.impl-work/<spec-name>/summary.json

  {
    \"task\": \"§X.Y — [requirement]\",
    \"status\": \"complete\",
    \"files_changed\": [\"path/to/file.py\"],
    \"concerns\": [],
    \"self_review\": \"Brief note on what self-review found, or empty\",
    \"digest\": {
      \"entities\": \"key classes, models, services touched\",
      \"patterns\": \"design patterns used or encountered\",
      \"complexity\": \"any algorithmic, state machine, auth, or business rule complexity\"
    }
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
mkdir -p <impl-dir>/.impl-work/<spec-name>/ && rm -f <impl-dir>/.impl-work/<spec-name>/summary.done
```

## After Agent Completes

1. Wait for `.done` marker (or note TaskOutput returns "Done.")
2. Read `<impl-dir>/.impl-work/<spec-name>/summary.json` for the structured summary
3. Check the `digest` field for complexity escalation (see `references/sub-agent-strategy.md`)
4. Run the full test suite — new tests should now pass, existing tests should still pass
5. If new tests still fail: fix the implementation (not the tests), then re-run
6. If a test seems genuinely wrong: **flag it for user review** rather than changing it
7. Do NOT re-analyse the agent's conversational output
