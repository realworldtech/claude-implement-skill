---
name: implement
description: Use this skill when implementing features from a specification document, business process document, or requirements document. Helps maintain connection to the source document throughout implementation and provides systematic verification.
argument-hint: <spec-path> | status [name] | verify [name] | continue [name] | list
user-invocable: true
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, TaskCreate, TaskUpdate, TaskList, TaskGet
---

# Implementation Skill

This skill helps you implement features from specification documents while maintaining a persistent connection to the source requirements. It solves the problem of "drift" where Claude loses track of the original document as work progresses and context compacts.

## Commands

| Command | Description |
|---------|-------------|
| `/implement <path-to-spec.md>` | Start planning implementation from a spec document |
| `/implement status [spec-name]` | Show current implementation progress |
| `/implement verify [spec-name]` | Run systematic verification against the spec |
| `/implement continue [spec-name]` | Resume implementation from where you left off |
| `/implement list` | List all active implementation trackers |

**Note**: `[spec-name]` is optional. If omitted and multiple trackers exist, you'll be prompted to choose. The spec-name is the basename without path or extension (e.g., for `docs/billing-spec.md`, use `billing-spec`).

## Core Principle: Section References as Anchors

The key insight is that **section references (e.g., §2.4, §9.1, Section 3.2) are stable anchors** that survive context compaction. Every task, every tracker entry, and every verification item should reference specific sections from the source document.

---

## Phase 1: Planning (`/implement <spec-path>`)

When the user provides a spec path, follow these steps:

### Step 1: Read and Parse the Specification

1. Read the entire specification document
2. Identify the document's section structure (look for patterns like `## Section N`, `### N.M`, `§N.M`, numbered headings)
3. Extract each discrete requirement with its section reference

### Step 2: Create the Implementation Tracker

Create a tracker file **named after the spec** in the current working directory. This allows multiple implementations to coexist.

**Naming convention**: `.impl-tracker-<spec-basename>.md`

Examples:
- Spec: `docs/kaylee-billing-spec.md` → Tracker: `.impl-tracker-kaylee-billing-spec.md`
- Spec: `notification-system.md` → Tracker: `.impl-tracker-notification-system.md`
- Spec: `../specs/auth-flow.md` → Tracker: `.impl-tracker-auth-flow.md`

This file is the **bridge** between compacted context and the source document.

Use this format:

```markdown
# Implementation Tracker

**Specification**: <path-to-spec>
**Created**: <date>
**Last Updated**: <date>

## Requirements Matrix

| Section | Requirement | Status | Implementation Notes |
|---------|-------------|--------|---------------------|
| §2.1 | Trigger on new ticket | pending | |
| §2.2 | Trigger on ticket close | pending | |
| §2.4 | Detect merged tickets | pending | |
| §9.1 | Extract follow-up actions | pending | |

## Implementation Log

### <date> - Session Start
- Parsed specification: <path>
- Identified N requirements across M sections
- Key areas: <list major sections>
```

### Step 3: Create Tasks with Section References

For each major requirement or group of related requirements:

1. Create a task using TaskCreate
2. Include the section reference in both subject and description
3. Add the spec section to task metadata

Example task subject: `Implement merge detection workflow (§2.4, §10.2)`

Example task description:
```
Implement the merged ticket detection and summary posting per §2.4 and §10.2.

Requirements from spec:
- Detect when a ticket is merged (§2.4)
- Skip standard billability assessment (§2.4)
- Generate merge summary in specified format (§10.2)
- Post summary to TARGET ticket as internal comment (§10.2)

Before starting: Re-read §2.4 and §10.2 from the spec.
```

### Step 4: Present the Plan

Show the user:
1. A summary of the specification structure
2. The requirements matrix from the tracker
3. The proposed task breakdown
4. Any questions about ambiguous requirements or implementation approach

Ask for approval before proceeding.

---

## Phase 2: Implementation

### Before Starting Each Task

**CRITICAL**: Before beginning work on any task:

1. Read the tracker file to get the section references
2. **Re-read the relevant section(s) from the original spec document**
3. Note any specific requirements, formats, or constraints mentioned

This prevents drift by ensuring you're always working from the source of truth.

### During Implementation

1. Implement according to the spec requirements
2. Note which files you're modifying and why
3. If you discover the spec is ambiguous or has gaps, note this and ask the user

### After Completing Each Task

1. Update the tracker file:
   - Change status from `pending` to `complete` or `partial`
   - Add implementation notes with file:line references
   - Add entry to Implementation Log

2. Update the task status using TaskUpdate

Example tracker update:
```markdown
| §2.4 | Detect merged tickets | complete | EdgeCaseHandler.check_merge() at src/handlers.py:156 |
```

---

## Phase 3: Verification (`/implement verify [spec-name]`)

When the user requests verification:

### Finding the Right Tracker

1. If spec-name provided: Look for `.impl-tracker-<spec-name>.md`
2. If not provided: List all `.impl-tracker-*.md` files in current directory
   - If exactly one: use it
   - If multiple: show list and ask which one
   - If none: inform user no active implementations found

### Step 1: Re-read the Entire Specification

Read the tracker to get the spec path, then read the full spec document fresh. Do not rely on compacted context.

### Step 2: Systematic Section-by-Section Review

For each section in the spec:

1. Read the section's requirements
2. Check the tracker for claimed implementation
3. Verify the actual code matches the requirement
4. Assess status: Implemented / Partial / Gap / Not Applicable

### Step 3: Generate Gap Analysis

Produce a structured report like this:

```markdown
## Gap Analysis: <Spec Name>

### Section N: <Section Title>

| Spec Section | Requirement | Status | Notes |
|--------------|-------------|--------|-------|
| §N.1 | <requirement> | Complete | <implementation location> |
| §N.2 | <requirement> | Partial | <what's missing> |
| §N.3 | <requirement> | GAP | <not implemented> |

### Gap Details

#### §N.2 - <Requirement Name>
**Spec says**: <exact quote from spec>
**Current state**: <what's actually implemented>
**Gap**: <what's missing>
**Suggested fix**: <how to address>

### Summary

| Status | Count |
|--------|-------|
| Complete | X |
| Partial | Y |
| Gap | Z |
| N/A | W |

### Priority Gaps
1. [HIGH] §X.Y - <description>
2. [MEDIUM] §A.B - <description>
```

---

## Phase 4: Status (`/implement status [spec-name]`)

When the user requests status:

### Finding the Right Tracker

1. If spec-name provided: Look for `.impl-tracker-<spec-name>.md`
2. If not provided: List all `.impl-tracker-*.md` files in current directory
   - If exactly one: use it
   - If multiple: show list and ask which one
   - If none: inform user no active implementations found

### Show Status

1. Read the tracker file
2. Read the current task list
3. Present a summary:
   - Overall progress (X of Y requirements complete)
   - Current task being worked on
   - Blockers or gaps discovered
   - Sections not yet started

---

## Phase 5: Continue (`/implement continue [spec-name]`)

When resuming work:

### Finding the Right Tracker

1. If spec-name provided: Look for `.impl-tracker-<spec-name>.md`
2. If not provided: List all `.impl-tracker-*.md` files in current directory
   - If exactly one: use it
   - If multiple: show list and ask which one
   - If none: inform user no active implementations found

### Resume Work

1. Read the tracker file to understand current state
2. Read the task list
3. Identify the next pending task
4. **Re-read the relevant spec sections** before continuing
5. Resume implementation

---

## Best Practices

### Writing Specs for This Workflow

Specs work best with this skill when they:
- Use numbered sections (§1.1, §2.3, etc.)
- Have discrete, testable requirements
- Include expected inputs/outputs where applicable
- Separate "must have" from "nice to have"

### Handling Spec Ambiguity

When the spec is unclear:
1. Note the ambiguity in the tracker
2. Ask the user for clarification
3. Document the decision made

### Handling Implementation Drift

If you notice you've deviated from the spec:
1. Stop and re-read the relevant section
2. Assess whether the deviation is intentional or accidental
3. Either correct the implementation or note the intentional deviation in the tracker

---

## Arguments Handling

The `$ARGUMENTS` variable contains what the user passed after `/implement`.

Parse it as follows:
- If it's a file path (contains `/` or ends in `.md`): Start planning phase
- If it starts with `status`: Show status (optional spec-name follows)
- If it starts with `verify`: Run verification (optional spec-name follows)
- If it starts with `continue`: Resume work (optional spec-name follows)
- If it's `list`: List all `.impl-tracker-*.md` files with their spec paths and status summaries
- If empty: Check for trackers, if exactly one exists offer to continue, if multiple list them, if none ask for spec path

### Tracker Discovery

To find trackers, glob for `.impl-tracker-*.md` in the current directory. Each tracker contains a `**Specification**:` line that points back to the original spec file.

Arguments: $ARGUMENTS
