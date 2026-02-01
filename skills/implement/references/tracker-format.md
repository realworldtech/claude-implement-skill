# Implementation Tracker Format

The tracker file (`.impl-tracker-<spec-name>.md`) serves as the persistent bridge between compacted context and the source specification. Even when Claude's memory of the conversation fades, reading this file provides enough context to continue work accurately.

## Naming Convention

Tracker files are named after their spec to allow multiple implementations:

| Spec Path | Tracker Filename |
|-----------|------------------|
| `docs/billing-spec.md` | `.impl-tracker-billing-spec.md` |
| `notification-system.md` | `.impl-tracker-notification-system.md` |
| `../specs/auth-flow.md` | `.impl-tracker-auth-flow.md` |

This allows you to work on multiple specs simultaneously without conflicts.

## Full Tracker Template

```markdown
# Implementation Tracker

**Specification**: path/to/spec.md
**Created**: YYYY-MM-DD
**Last Updated**: YYYY-MM-DD
**Status**: Planning | In Progress | Verification | Complete

## Recovery Instructions

If you're reading this after context compaction or in a new session, follow these steps:

1. **You are implementing a specification**. The spec path is shown above.
2. **Read this entire tracker** to understand current state and progress.
3. **Read the specification file** to understand requirements.
4. **Check TaskList** for pending tasks.
5. **Re-read relevant spec sections** (noted in Requirements Matrix) before any implementation work.
6. **Delegate implementation to sub-agents**:
   - Straightforward tasks (adding fields, simple CRUD): use `model: "sonnet"` or `"haiku"`
   - Moderate/complex tasks (logic, algorithms): use `model: "opus"`
7. **Use Opus for verification** and fixing issues (`model: "opus"` - always).
8. **Update this tracker** after each completed task.

Key workflow: Tracker → Spec sections → Sub-agent → Verify → Update tracker

## Specification Summary

Brief description of what the spec covers and the major functional areas.

### Key Sections
- Section 2: <title> - <brief description>
- Section 3: <title> - <brief description>
- ...

## Requirements Matrix

| Section | Requirement | Priority | Status | Implementation | Tests |
|---------|-------------|----------|--------|----------------|-------|
| §2.1 | In-flight triggers | Must | complete | src/triggers.py:45 | test_triggers.py:12 |
| §2.2 | Closure triggers | Must | complete | src/triggers.py:78 | test_triggers.py:34 |
| §2.4 | Merge detection | Must | partial | EdgeCaseHandler | - |
| §9.1 | Follow-up extraction | Should | pending | - | - |

### Status Legend
- `pending` - Not started
- `in_progress` - Currently being implemented
- `partial` - Partially implemented, gaps identified
- `complete` - Fully implemented and verified
- `blocked` - Cannot proceed, see notes
- `n/a` - Not applicable to this implementation

### Priority Legend
- `Must` - Required for spec compliance
- `Should` - Expected but not blocking
- `Could` - Nice to have
- `Won't` - Explicitly out of scope

## Known Gaps

Gaps discovered during implementation or verification that need attention.

### GAP-001: Merge workflow incomplete (§2.4, §10.2)
- **Discovered**: YYYY-MM-DD
- **Severity**: High
- **Description**: Detects merge but doesn't post to target ticket
- **Spec requirement**: Post summary to TARGET ticket as internal comment
- **Current behavior**: Only detects merge, skips further processing
- **Proposed fix**: Add target ticket lookup and comment posting
- **Status**: Open

## Deviations from Spec

Intentional deviations with rationale.

### DEV-001: Simplified token chunking (§3.1)
- **Spec says**: Chunk at 8000 tokens with overlap
- **Implementation**: Chunk at 6000 tokens, no overlap
- **Rationale**: User requested simpler approach for initial version
- **Approved by**: User on YYYY-MM-DD

## Implementation Log

Chronological log of implementation sessions.

### YYYY-MM-DD - Session 1: Initial Setup
- Parsed specification
- Created tracker
- Identified 24 requirements across 13 sections
- Created 8 implementation tasks
- Completed: §2.1 (triggers), §2.2 (closure triggers)

### YYYY-MM-DD - Session 2: Core Processing
- Re-read §3, §4 before starting
- Implemented comment classification (§3.2)
- Implemented billability rules (§4.1-4.4)
- Discovered gap in §4.7 (MSA scope)
- Added GAP-001 to tracker

### YYYY-MM-DD - Session 3: Verification
- Ran full verification against spec
- 18 complete, 4 partial, 2 gaps
- Updated requirements matrix
- Prioritized remaining work
```

## Why Each Section Matters

### Specification Summary
Helps quickly re-orient when resuming work. Even a compacted context can use this to understand the domain.

### Requirements Matrix
The core tracking table. Must be kept up-to-date after every task completion. File:line references allow quick navigation to implementation.

### Known Gaps
Prevents losing track of identified issues. Each gap has enough context to be actionable even without full conversation history.

### Deviations
Documents intentional divergence from spec. Prevents future confusion about whether something is a bug or a feature.

### Implementation Log
Provides session-by-session history. Useful for understanding what was done and in what order.

## Updating the Tracker

### After completing a task:
1. Update the row in Requirements Matrix
2. Add file:line reference to Implementation column
3. Add test reference if tests were added
4. Add entry to Implementation Log

### After discovering a gap:
1. Add entry to Known Gaps section
2. Update Requirements Matrix status to `partial` or `blocked`
3. Note in Implementation Log

### After verification:
1. Update all statuses in Requirements Matrix
2. Add new gaps to Known Gaps
3. Update Implementation Log with verification results

## Machine-Readable Sections

For programmatic parsing, the tracker includes structured sections that can be extracted:

```markdown
<!-- SPEC_PATH: path/to/spec.md -->
<!-- LAST_SECTION: §4.7 -->
<!-- COMPLETE_COUNT: 18 -->
<!-- PARTIAL_COUNT: 4 -->
<!-- GAP_COUNT: 2 -->
<!-- PENDING_COUNT: 0 -->
```

These comments can be used by scripts or future Claude sessions to quickly assess state.
