# Design: SKILL.md Restructure for Context Efficiency

**Date:** 2026-02-18
**Status:** Approved

## Problem

SKILL.md has grown to 1403 lines — nearly 3x the recommended 500-line max. Every invocation loads all phases, all prompt templates, and all structural details into context, wasting tokens on content that isn't needed for the current operation.

## Solution

Restructure into a routing document (SKILL.md) that loads detailed phase workflows and prompt templates on demand from reference files.

## File Layout

```
skills/implement/
  SKILL.md                          # ~400-500 lines, routing + summaries
  references/
    tracker-format.md               # (existing) full tracker template + explanation
    workflow-quick-ref.md           # (existing) checklists
    sub-agent-strategy.md           # model selection, routing, DIGEST, delegation
    phase-1-planning.md             # full Phase 1 workflow
    phase-2-implementation.md       # standard workflow
    phase-2-tdd.md                  # TDD workflow
    phase-3-verification.md         # full verification machinery
    phase-5-continue.md             # resume + spec evolution
  prompts/
    implement-single-file.md        # Task() template for single-file spec
    implement-multi-file.md         # Task() template for multi-file spec
    write-tests.md                  # test writing prompt
    fix-issue.md                    # fix sub-agent prompt
    tdd-write-tests.md              # TDD test-first prompt
    tdd-implement.md                # TDD implement-to-pass prompt
    verify-requirement.md           # verification sub-agent prompt
    reverify-requirement.md         # re-verification prompt
    fix-verification-gap.md         # fix gap prompt
  examples/
    sample-spec.md                  # (existing)
```

## SKILL.md Structure (after restructure)

1. Front matter
2. Commands table
3. Preferences (brief)
4. Core Principle
5. Phase summaries (2-3 sentences each) with "Read references/<file> for details"
6. Phase 4 Status inline (24 lines, not worth extracting)
7. Critical rules
8. Implicit activation
9. Arguments handling / routing
10. Recovery overview

## Reference Loading Pattern

Each phase summary in SKILL.md says:
> **Read `references/phase-N-xxx.md` for the detailed workflow.**

Phase reference files say:
> **Use the prompt template at `prompts/xxx.md` when delegating.**

Two levels of indirection, each loaded only when needed.
