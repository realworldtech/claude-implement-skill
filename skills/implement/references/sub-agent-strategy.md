# Sub-Agent Delegation Strategy

To preserve context in long implementations, delegate actual coding work to sub-agents while keeping orchestration in the main conversation.

## Model Selection

Choose the model based on task complexity:

| Task Complexity | Model | Examples |
|-----------------|-------|----------|
| Straightforward | `haiku` or `sonnet` | Adding a field, simple CRUD, boilerplate code |
| Moderate/Complex | `opus` | Logic decisions, algorithmic work, state management |
| Verification | `opus` | Always use Opus - catches subtle gaps |
| Fixing issues | `opus` | Always use Opus - requires understanding root cause |

**Rule of thumb**: If the task involves any logic decisions, conditional behavior, or algorithmic thinking, use `opus`. When in doubt, use `opus` - the cost savings from using smaller models aren't worth missing implementation details.

## Size-Based Routing for Large Specs

When a spec has breakout section files (e.g., produced by `/spec`), build a structural index before delegating work:

1. **Build the index**: Run `wc -c` on each section file. Estimate tokens: `estimated_tokens ≈ file_size_bytes / 4`
2. **Route by section size**:

| Section Size | Model | Grouping |
|-------------|-------|----------|
| < 5k tokens | `sonnet` | Group 2-3 sections per agent |
| 5k–20k tokens | `sonnet` | 1 section per agent |
| > 20k tokens | `opus` | 1 section per agent |

3. **Digest-based complexity escalation**: Sonnet agents produce a DIGEST (5-10 lines) at the end of their response summarizing key entities, patterns, and complexity encountered. The main conversation checks the DIGEST against the complexity category table:

   | Category | DIGEST signals | Why opus review needed |
   |----------|---------------|----------------------|
   | Algorithms | "algorithm", "calculation", "formula", "heuristic" | Subtle correctness |
   | State machines | "state machine", "state transition", "lifecycle" | Complex interactions |
   | Permission/auth | "permission", "role inheritance", "RBAC", "access control" | Security boundaries |
   | Complex business rules | "conditional", "override", "exception", "cascading" | Edge cases |
   | Cross-cutting | "affects all", "global constraint", "system-wide" | Holistic view |

   Escalation is **MANDATORY** when a DIGEST matches any category — it is not discretionary. When matched: dispatch opus to REVIEW sonnet's code changes with focus on the flagged area. Do NOT rationalize skipping the review.

**Sub-split sections**: When a section was split into sub-files (e.g., `02a-`, `02b-`, `02c-`), each sub-file routes independently by its own size. Tasks referencing the parent section (e.g., §2) should include all sub-file paths in the sub-agent prompt.

**Note**: This only applies when the spec has breakout section files. Single-file specs use the standard model selection table above.

## When to Delegate

**Delegate to a sub-agent when:**
- Implementing a discrete requirement (1-3 section references)
- The task has clear inputs (spec sections) and outputs (code changes)
- The main conversation context is getting large

**Keep in main conversation:**
- Planning and orchestration
- Reading/updating the tracker
- User interactions and decisions
- Final verification review

## Sub-Agent Task Pattern

When delegating implementation work:

1. **Prepare context** (main conversation):
   - Read the tracker for section references
   - Read the relevant spec sections
   - Identify relevant existing code files

2. **Delegate to sub-agent** using the appropriate prompt template from `prompts/`:
   - Single-file spec: `prompts/implement-single-file.md`
   - Multi-file spec: `prompts/implement-multi-file.md`
   - Test writing: `prompts/write-tests.md`
   - TDD test-first: `prompts/tdd-write-tests.md`
   - TDD implementation: `prompts/tdd-implement.md`
   - Fixing issues: `prompts/fix-issue.md`

3. **After sub-agent completes** (main conversation):
   - Sub-agent output comes via `TaskOutput` — use that directly
   - **Do NOT read or grep agent output files** — they are raw JSON transcripts, not usable text
   - Review the changes made
   - If issues found, fix with `Task` using `model: "opus"` (see `prompts/fix-issue.md`)
   - Update the tracker with implementation notes
   - Update task status
