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

  ## Important
  - Make the failing tests pass
  - Don't modify the tests
  - Also ensure existing tests still pass
  - Summarize what you changed and any issues encountered

  At the end of your response, include a DIGEST section:
  === DIGEST ===
  - Entities: <key classes, models, services touched>
  - Patterns: <design patterns used or encountered>
  - Complexity: <any algorithmic, state machine, auth, or business rule complexity>
  === END DIGEST ==="
)
```

## After Implementation

1. **Check DIGEST** for complexity escalation (see `references/sub-agent-strategy.md`)
2. Run the full test suite — new tests should now pass, existing tests should still pass
3. If new tests still fail: fix the implementation (not the tests), then re-run
4. If a test seems genuinely wrong: **flag it for user review** rather than changing it
5. If existing tests break: fix the regression in the implementation
