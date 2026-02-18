# Test Writing Prompt — Standard Workflow

Use this template when delegating test writing after implementation is reviewed and existing tests pass. This is Phase 2 Step 4 (standard workflow).

**Model selection**: Use `sonnet` for most tests, `opus` for complex logic or algorithm tests.

```
Task(
  subagent_type: "general-purpose",
  model: "sonnet",  // Use "opus" for complex logic or algorithm tests
  prompt: "Write tests for the implementation of §X.Y.

  ## Spec Requirement (§X.Y)
  [Quote the spec text - this defines WHAT to test]

  ## Implementation
  [List files and key functions/classes that were implemented]

  ## Test Expectations
  - [Specific behaviors to verify, derived from the spec]

  ## Existing Test Patterns
  [Show an example from the existing test suite so tests match project conventions]

  ## Before You Begin

  If anything is unclear about what to test or how the implementation should
  behave — ask. It's better to clarify now than to write tests against wrong assumptions.

  ## Guidelines
  - Each test should verify a specific spec requirement or behavior
  - Do not write trivial or boilerplate tests
  - Include edge cases mentioned in the spec
  - Use descriptive test names that reference the requirement

  ## Output — Write summary to disk

  Write your summary to: <impl-dir>/.impl-work/<spec-name>/summary.json

  {
    \"task\": \"tests for §X.Y\",
    \"status\": \"complete\",
    \"files_changed\": [\"tests/test_file.py\"],
    \"tests_written\": [\"test name — what it verifies\"],
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

## After Agent Completes

1. Read `<impl-dir>/.impl-work/<spec-name>/summary.json` for the test summary
2. **Run the full test suite** to confirm both new and existing tests pass
3. Do NOT re-analyse the agent's conversational output

## What to Test

Focus on meaningful, spec-driven tests:

- Does this endpoint/view exist and respond correctly?
- Do permissions and access controls work as specified?
- Does this algorithm/logic produce correct results for spec-defined scenarios?
- Do error cases behave as the spec requires?

Do NOT write trivial tests (testing that a constant equals itself, testing framework boilerplate, testing Python's built-in behavior). Every test should verify a requirement or behavior from the spec.

If the spec doesn't clearly define expected behavior for a piece of functionality, and you can't reasonably infer it from context, **ask the user** before writing tests.
