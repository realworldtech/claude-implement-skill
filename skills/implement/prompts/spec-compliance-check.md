# Spec Compliance Check — Per-Task

Use this template for a lightweight post-task spec compliance check. This runs after implementation (and tests) but before marking the task complete. It catches drift early rather than waiting for Phase 3 verification.

**This is optional but recommended.** Skip it only when the task is trivially simple (e.g., adding a single field with no logic).

**Model selection**: Use `sonnet` for most checks. Use `opus` if the task involved complex logic or multiple interacting requirements.

```
Task(
  subagent_type: "general-purpose",
  model: "sonnet",
  prompt: "Review whether an implementation matches its specification.

  ## What Was Requested (§X.Y)

  [Exact spec text for this task's requirements]

  ## What the Implementer Claims

  [Summary from the implementation sub-agent's report]

  ## CRITICAL: Verify Independently

  Do NOT trust the implementer's report at face value. They may have been
  optimistic, missed details, or misinterpreted the spec. You MUST verify
  by reading the actual code.

  ## Your Job

  Read the implementation code and check:

  **Missing requirements:**
  - Is everything from the spec actually implemented?
  - Are there requirements that were skipped or only partially done?

  **Extra/unneeded work:**
  - Was anything built that wasn't in the spec?
  - Any over-engineering or speculative features?

  **Misunderstandings:**
  - Was the spec interpreted correctly?
  - Does the implementation match the spec's intent, not just its letter?

  ## Files to Check
  - [list implementation files from the sub-agent's report]

  ## Report

  - **PASS** — implementation matches spec for this task
  - **ISSUES** — list specifically what's missing, extra, or wrong, with file:line references

  Keep it brief. This is a spot-check, not a full audit."
)
```

## When to Use

Use this after:
1. The implementation sub-agent has completed
2. Tests have been run and pass
3. DIGEST escalation has been handled (if applicable)

And before:
4. Updating the tracker to `complete`

## When to Skip

- Trivially simple tasks (single field addition, config change)
- Tasks where the implementation agent used `opus` and the self-review was thorough
- When you're about to run full Phase 3 verification anyway

## If Issues Are Found

1. Fix the issues (use `prompts/fix-issue.md` for complex fixes)
2. Re-run tests
3. You do NOT need to re-run the compliance check — the fix agent + tests are sufficient
