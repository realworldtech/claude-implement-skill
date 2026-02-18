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

  After implementation, summarize what you changed and any issues encountered."
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
