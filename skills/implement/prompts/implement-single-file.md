# Implementation Prompt — Single-File Spec

Use this template when delegating implementation work for a single-file spec. Embed the spec text directly in the prompt.

**Model selection**: Use `sonnet` for straightforward tasks, `opus` for logic/algorithms. See `references/sub-agent-strategy.md` for details.

```
Task(
  subagent_type: "general-purpose",
  model: "sonnet",  // Use "opus" if task involves logic/algorithms
  prompt: "Implement [requirement] per §X.Y of the specification.

  ## Spec Requirement (§X.Y)
  [Quote the exact spec text here]

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

  ## Report Format

  Summarize: what you implemented, files changed, any issues or concerns,
  and self-review findings (if any)."
)
```

## Placeholders

| Placeholder | Replace with |
|-------------|-------------|
| `[requirement]` | One-line description of the requirement |
| `§X.Y` | Section reference from the spec |
| `[Quote the exact spec text here]` | Verbatim spec text for this requirement |
| `path/to/file.py` | Actual file paths to modify |
| `[Any relevant existing code patterns...]` | Existing patterns the agent should follow |
| `[Describe what the implementation should do]` | Expected behavior after implementation |
