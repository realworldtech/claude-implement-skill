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

  [Summary from the implementation summary.json — paste the relevant fields]

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
  - [list implementation files from the summary.json]

  ## Output — Write verdict to disk

  Write your verdict to: <impl-dir>/.impl-work/<spec-name>/compliance.json

  {
    \"task\": \"§X.Y compliance check\",
    \"verdict\": \"pass\",
    \"issues\": []
  }

  Or if issues found:

  {
    \"task\": \"§X.Y compliance check\",
    \"verdict\": \"issues\",
    \"issues\": [
      {\"type\": \"missing\", \"description\": \"...\", \"file\": \"...\", \"line\": \"...\"},
      {\"type\": \"extra\", \"description\": \"...\", \"file\": \"...\", \"line\": \"...\"},
      {\"type\": \"misunderstanding\", \"description\": \"...\", \"file\": \"...\", \"line\": \"...\"}
    ]
  }

  After writing the JSON, write a completion marker:
  <impl-dir>/.impl-work/<spec-name>/compliance.done (contents: just \"done\").
  The .done marker MUST be the last file you write.

  Then respond with just: Done."
)
```

## Pre-flight

Before dispatching, clear any previous markers:

```bash
rm -f <impl-dir>/.impl-work/<spec-name>/compliance.done
```

## After Agent Completes

1. Read `<impl-dir>/.impl-work/<spec-name>/compliance.json` for the verdict
2. If `verdict` is `pass` — proceed to tracker update
3. If `verdict` is `issues` — fix them (use `prompts/fix-issue.md` for complex fixes), re-run tests
4. You do NOT need to re-run the compliance check after fixes — the fix agent + tests are sufficient
5. Do NOT re-analyse the agent's conversational output

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
