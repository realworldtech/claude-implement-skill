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
**TDD Mode**: on | off
**Spec Type**: single-file | multi-file
**Spec Baseline**: YYYY-MM-DD
**Worktree**: <absolute path to worktree, or "none" if working in current directory>
**Branch**: <branch name, or "none" if not specified>

## Recovery Instructions

If you're reading this after context compaction or in a new session, follow these steps:

1. **You are implementing a specification**. The spec path is shown above.
2. **Read this entire tracker** to understand current state and progress.
3. **Check the Worktree field above**: If not `none`, validate the worktree path still exists on disk and is a valid git worktree. Set it as the implementation directory — all file operations should target that path. If the worktree no longer exists, warn the user.
4. **Check the Spec Type field above**:
   - **single-file**: Read the full spec file to understand requirements.
   - **multi-file**: Read the master spec's table of contents only. Run `wc -c` on section files to rebuild the structural index (`estimated_tokens ≈ bytes / 4`). Compare against the stored Structural Index — look for new files, removed files, >20% size changes, or new sub-split patterns (e.g., `02a-`, `02b-`). If changes are detected, flag them before proceeding (see Spec Evolution Handling in SKILL.md). Do NOT read all section files into main context — pass file paths to sub-agents and let them read the files directly.
5. **Check TaskList** for pending tasks.
6. **Re-read relevant spec sections** (noted in Requirements Matrix) before any implementation work. For multi-file specs, read only the section headings and requirement identifiers — sub-agents will read full sections.
7. **Delegate implementation to sub-agents**:
   - Straightforward tasks (adding fields, simple CRUD): use `model: "sonnet"` or `"haiku"`
   - Moderate/complex tasks (logic, algorithms): use `model: "opus"`
   - For multi-file specs, route by section size: <5k tokens → sonnet (group 2-3), 5k-20k → sonnet (1 each), >20k → opus (1 each)
   - **DIGEST-based escalation**: Sonnet agents produce a `=== DIGEST ===` at end of response. Check DIGEST signals against complexity categories (algorithms, state machines, permission/auth, complex business rules, cross-cutting). If matched → mandatory opus review of sonnet's changes.
8. **Run tests after each sub-agent completes** - never skip this step.
9. **Use Opus for verification** and fixing issues (`model: "opus"` - always).
10. **Update this tracker** after each completed task.

Key workflow: Tracker → Spec sections → Sub-agent → **Run tests** → Verify → Update tracker

**CRITICAL**: Never mark tasks complete or claim "done" without running tests first. Field name typos, import errors, and type mismatches are caught by testing, not spec verification.

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

## Structural Index

<!-- STRUCTURAL_INDEX
file: sections/01-overview.md | bytes: 3200 | tokens: 800 | route: sonnet | parent: §1
file: sections/02a-core-model.md | bytes: 18400 | tokens: 4600 | route: sonnet | parent: §2
file: sections/02b-core-relations.md | bytes: 22000 | tokens: 5500 | route: sonnet | parent: §2
file: sections/02c-core-validation.md | bytes: 31200 | tokens: 7800 | route: sonnet | parent: §2
file: sections/03-api.md | bytes: 45600 | tokens: 11400 | route: sonnet | parent: §3
file: sections/04-auth.md | bytes: 88000 | tokens: 22000 | route: opus | parent: §4
-->

| File | Bytes | Est. Tokens | Model Route | Parent Section |
|------|-------|-------------|-------------|----------------|
| `sections/01-overview.md` | 3,200 | 800 | sonnet | §1 |
| `sections/02a-core-model.md` | 18,400 | 4,600 | sonnet | §2 |
| `sections/02b-core-relations.md` | 22,000 | 5,500 | sonnet | §2 |
| `sections/02c-core-validation.md` | 31,200 | 7,800 | sonnet | §2 |
| `sections/03-api.md` | 45,600 | 11,400 | sonnet | §3 |
| `sections/04-auth.md` | 88,000 | 22,000 | opus | §4 |

**Baseline captured**: YYYY-MM-DD

*Note: Sub-split files (e.g., `02a-`, `02b-`, `02c-`) are grouped under their parent section number. A task referencing §2 may require reading all sub-files. This index is only populated for multi-file specs.*

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

### Header Fields (TDD Mode)
The `**TDD Mode**:` field records whether Test-Driven Development workflow is active for this implementation. Set during Phase 1 planning and read by `/implement continue` to determine which workflow to follow. Values are `on` or `off`.

### Header Fields (Spec Type)
The `**Spec Type**:` field records whether the spec is a single file or has breakout section files. Set during Phase 1 parsing. Values are `single-file` or `multi-file`. This tells `/implement continue` and recovery sessions whether to use the structural index approach (pass file paths to sub-agents) or the standard approach (embed spec text in prompts).

### Specification Summary
Helps quickly re-orient when resuming work. Even a compacted context can use this to understand the domain.

### Requirements Matrix
The core tracking table. Must be kept up-to-date after every task completion. File:line references allow quick navigation to implementation. **The Tests column tracks test coverage** - a requirement is not truly complete until tests pass.

### Structural Index
Records the byte sizes, estimated token counts, and model routing for each section file in a multi-file spec. Used as the **spec baseline** — when resuming work across sessions, re-run `wc -c` and compare against this index to detect spec changes (new files, removed files, size changes, sub-splits). The machine-readable `<!-- STRUCTURAL_INDEX ... -->` comment enables automated parsing. Only populated for multi-file specs.

### Known Gaps
Prevents losing track of identified issues. Each gap has enough context to be actionable even without full conversation history.

### Deviations
Documents intentional divergence from spec. Prevents future confusion about whether something is a bug or a feature.

### Implementation Log
Provides session-by-session history. Useful for understanding what was done and in what order.

## Updating the Tracker

### After completing a task:
1. **Run tests first** - never mark complete without validating code works
2. Update the row in Requirements Matrix
3. Add file:line reference to Implementation column
4. Add test reference if tests were added (or note "manual validation" if no tests)
5. Add entry to Implementation Log

### After discovering a gap:
1. Add entry to Known Gaps section
2. Update Requirements Matrix status to `partial` or `blocked`
3. Note in Implementation Log

### After verification:
1. **Run full test suite first** - verification is meaningless if tests fail
2. Update all statuses in Requirements Matrix
3. Add new gaps to Known Gaps
4. Update Implementation Log with verification results
5. Note test pass/fail status in log entry
6. Verification reports stored in `.impl-verification/<spec-name>/`

### Before claiming "Done":
1. All tests pass
2. Linting/type checks pass (if configured)
3. Application starts/compiles without errors
4. All requirement statuses are `complete` or documented as `n/a`

## Machine-Readable Sections

For programmatic parsing, the tracker includes structured sections that can be extracted:

```markdown
<!-- SPEC_PATH: path/to/spec.md -->
<!-- TDD_MODE: on|off -->
<!-- SPEC_TYPE: single-file|multi-file -->
<!-- SPEC_BASELINE: YYYY-MM-DD -->
<!-- WORKTREE: /absolute/path/or/none -->
<!-- BRANCH: branch-name-or-none -->
<!-- LAST_SECTION: §4.7 -->
<!-- COMPLETE_COUNT: 18 -->
<!-- PARTIAL_COUNT: 4 -->
<!-- GAP_COUNT: 2 -->
<!-- PENDING_COUNT: 0 -->
```

These comments can be used by scripts or future Claude sessions to quickly assess state.
