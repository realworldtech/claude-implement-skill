# TDD Test-First Prompt

Use this template when writing tests BEFORE implementation exists (TDD Mode, Phase 2 TDD Step 2). The sub-agent works purely from the spec — it should NOT see any implementation code.

**Model selection**: Use `sonnet` for most tests, `opus` for complex logic or algorithm tests.

**For multi-file specs**: Pass the section file path instead of quoting the full text. Include the structural index so the agent understands the full spec layout.

```
Task(
  subagent_type: "general-purpose",
  model: "sonnet",  // Use "opus" for complex logic or algorithm tests
  prompt: "Write tests for §X.Y BEFORE implementation exists.

  ## Spec Requirement (§X.Y)
  [Exact spec text — or for multi-file specs: 'Read the spec section at: path/to/sections/section-X.md']

  ## What to Test
  Write tests that verify the spec requirements are met.
  These tests SHOULD FAIL right now — that's expected and correct.

  ## Project Test Conventions
  [Show existing test patterns/framework setup from the project]

  ## Before You Begin

  If anything is unclear about the spec requirements or how to test them — ask.
  It's better to clarify now than to write tests that don't match the intent.

  ## Important
  - Write tests from the SPEC, not from any existing code
  - Tests should be specific enough to catch wrong implementations
  - Include edge cases mentioned in the spec
  - Each test should verify one clear spec requirement
  - Tests MUST be runnable (correct imports, fixtures, etc.)
  - Do NOT stub/mock the thing being tested — test real behavior
  - Use descriptive test names that reference the requirement

  ## Output — Write summary to disk

  Write your summary to: <impl-dir>/.impl-work/<spec-name>/summary.json

  {
    \"task\": \"TDD tests for §X.Y\",
    \"status\": \"complete\",
    \"files_changed\": [\"tests/test_file.py\"],
    \"tests_written\": [\"test name — what spec requirement it verifies\"],
    \"concerns\": [],
    \"digest\": {
      \"entities\": \"key classes, models, services referenced\",
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
rm -f <impl-dir>/.impl-work/<spec-name>/summary.done
```

## After Tests are Written

1. Read `<impl-dir>/.impl-work/<spec-name>/summary.json` for the test summary
2. Run the test suite. The new tests **should fail** (since implementation doesn't exist yet). This validates:
   - Tests are checking something real (not trivially passing)
   - Tests are syntactically valid and runnable
   - Test infrastructure works
3. Do NOT re-analyse the agent's conversational output

**If tests pass unexpectedly**: Investigate — either the feature already exists, or tests are too loose.

**If tests error (import/syntax)**: Fix the test setup (imports, fixtures, file paths), not the test assertions. The assertions reflect the spec.
