# Implementation Workflow Instructions

Use these instructions when implementing features from a specification document. This workflow maintains connection to the source document throughout implementation and prevents drift.

## Core Principle

**Section references (e.g., Section 2.4, Section 9.1) are stable anchors.** Every task, every tracker entry, and every verification item should reference specific sections from the source document.

---

## Phase 1: Planning

When starting implementation from a spec document:

### Step 1: Parse the Specification

1. Read the entire specification document
2. Identify the section structure (look for numbered headings, Section N.M patterns)
3. Extract each discrete requirement with its section reference

### Step 2: Create the Tracker

Create a tracker document with this format:

```markdown
# Implementation Tracker

**Specification**: [document name]
**Created**: [date]
**Last Updated**: [date]

## Requirements Matrix

| Section | Requirement | Status | Implementation Notes |
|---------|-------------|--------|---------------------|
| Section 2.1 | [requirement] | pending | |
| Section 2.2 | [requirement] | pending | |

## Implementation Log

### [date] - Session Start
- Parsed specification
- Identified N requirements across M sections
```

### Step 3: Plan the Work

Break requirements into logical tasks, grouping related sections. For each task:
- Note which spec sections it addresses
- Note any dependencies on other tasks

Present the plan for approval before proceeding.

---

## Phase 2: Implementation

### Before Starting Each Task

**CRITICAL**: Before beginning work on any task:

1. Check the tracker for which sections this task addresses
2. **Re-read those sections from the original spec**
3. Note any specific requirements, formats, or constraints

This prevents drift by ensuring you're always working from the source of truth.

### After Completing Each Task

Update the tracker:
- Change status from `pending` to `complete` or `partial`
- Add implementation notes
- Add entry to Implementation Log

---

## Phase 3: Verification

When verifying the implementation:

### Step 1: Re-read the Entire Specification

Read the full spec document fresh. Do not rely on memory or summaries.

### Step 2: Section-by-Section Review

For each section in the spec:
1. Read the section's requirements
2. Check the tracker for claimed implementation
3. Verify the actual implementation matches the requirement
4. Assess status: Complete / Partial / Gap / Not Applicable

### Step 3: Generate Gap Analysis

Produce a structured report:

```markdown
## Gap Analysis

### Section N: [Section Title]

| Section | Requirement | Status | Notes |
|---------|-------------|--------|-------|
| Section N.1 | [requirement] | Complete | [location] |
| Section N.2 | [requirement] | Partial | [what's missing] |
| Section N.3 | [requirement] | GAP | [not implemented] |

### Gap Details

#### Section N.2 - [Requirement Name]
**Spec says**: [exact quote from spec]
**Current state**: [what's actually implemented]
**Gap**: [what's missing]
**Suggested fix**: [how to address]

### Summary

| Status | Count |
|--------|-------|
| Complete | X |
| Partial | Y |
| Gap | Z |

### Priority Gaps
1. [HIGH] Section X.Y - [description]
2. [MEDIUM] Section A.B - [description]
```

---

## Quick Reference

### Status Values
- `pending` - Not started
- `in_progress` - Currently working
- `partial` - Partially implemented, gaps identified
- `complete` - Fully implemented
- `blocked` - Cannot proceed
- `n/a` - Not applicable

### The Golden Rule

**Before touching any implementation, re-read the relevant spec section(s).**

This single habit prevents most implementation drift.

### Red Flags

Stop and re-read the spec if you notice:
- Implementing something not mentioned in spec
- Making assumptions about behaviour
- Saying "I think" instead of "the spec says"
- Skipping a requirement because it seems hard
