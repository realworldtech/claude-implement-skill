# Implementation Prompt — Multi-File Spec

Use this template when delegating implementation work for a multi-file spec (breakout sections). Pass file paths instead of embedded content — the sub-agent reads the section file itself.

**Model selection**: Route by section size — see `references/sub-agent-strategy.md` for the size-based routing table.

```
Task(
  subagent_type: "general-purpose",
  model: "sonnet",  // Route by section size — see Size-Based Routing table
  prompt: "Implement [requirement] per §X.Y of the specification.

  ## Spec Layout (structural index)
  [Paste the structural index so the agent knows the full spec layout]

  ## Section to Read
  Read the spec section at: path/to/sections/section-X.md
  Focus on the requirements in §X.Y.

  ## Requirement References
  - §X.Y.1: [one-line summary from Phase 1 extraction]
  - §X.Y.2: [one-line summary]

  ## Files to Modify
  - path/to/file.py (describe what changes needed)

  ## Context
  [Any relevant existing code patterns or constraints]

  ## Expected Outcome
  - [Describe what the implementation should do]

  ## Before You Begin

  If anything is unclear about the requirements, approach, or constraints — ask.
  It's better to clarify now than to implement the wrong thing.

  ## While You Work

  If you encounter something unexpected or need to make a judgment call, ask rather
  than guess. Don't make assumptions about ambiguous requirements.

  ## Before Reporting Back: Self-Review

  Before you report, review your own work:

  **Completeness**: Did I implement everything the spec requires for this section?
  Are there edge cases or constraints I missed?

  **Quality**: Are names clear and accurate? Is the code clean and maintainable?
  Does it follow existing patterns in the codebase?

  **Discipline**: Did I avoid overbuilding (YAGNI)? Did I only build what was
  requested? No extra features, no speculative abstractions?

  **Testing readiness**: Will this be straightforward to test? Are there any
  hidden dependencies that will make testing difficult?

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
3. Check the `digest` field against complexity categories in `references/sub-agent-strategy.md`
4. Do NOT re-analyse the agent's conversational output

## Placeholders

| Placeholder | Replace with |
|-------------|-------------|
| `[requirement]` | One-line description of the requirement |
| `§X.Y` | Section reference from the spec |
| `[Paste the structural index...]` | The structural index from the tracker |
| `path/to/sections/section-X.md` | Actual path to the section file |
| `[one-line summary...]` | Brief requirement summaries from Phase 1 extraction |
| `path/to/file.py` | Actual file paths to modify |
| `<impl-dir>` | Implementation directory (worktree or cwd) |
| `<spec-name>` | Spec basename for scoping |

## DIGEST

The `digest` field in the summary JSON replaces the inline `=== DIGEST ===` section. Check its signals against the complexity category table in `references/sub-agent-strategy.md`. If any category matches, dispatch an opus review.
