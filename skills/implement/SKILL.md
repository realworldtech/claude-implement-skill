---
name: implement
description: Use this skill when implementing features from a specification document, business process document, or requirements document. Helps maintain connection to the source document throughout implementation and provides systematic verification.
argument-hint: <spec-path> | status [name] | verify [name] | continue [name] | list
user-invocable: true
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, Task, TaskCreate, TaskUpdate, TaskList, TaskGet
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

## Sub-Agent Delegation Strategy

To preserve context in long implementations, delegate actual coding work to sub-agents while keeping orchestration in the main conversation.

### Model Selection

Choose the model based on task complexity:

| Task Complexity | Model | Examples |
|-----------------|-------|----------|
| Straightforward | `haiku` or `sonnet` | Adding a field, simple CRUD, boilerplate code |
| Moderate/Complex | `opus` | Logic decisions, algorithmic work, state management |
| Verification | `opus` | Always use Opus - catches subtle gaps |
| Fixing issues | `opus` | Always use Opus - requires understanding root cause |

**Rule of thumb**: If the task involves any logic decisions, conditional behavior, or algorithmic thinking, use `opus`. When in doubt, use `opus` - the cost savings from using smaller models aren't worth missing implementation details.

### When to Delegate

**Delegate to a sub-agent when:**
- Implementing a discrete requirement (1-3 section references)
- The task has clear inputs (spec sections) and outputs (code changes)
- The main conversation context is getting large

**Keep in main conversation:**
- Planning and orchestration
- Reading/updating the tracker
- User interactions and decisions
- Final verification review

### Sub-Agent Task Pattern

When delegating implementation work:

1. **Prepare context** (main conversation):
   - Read the tracker for section references
   - Read the relevant spec sections
   - Identify relevant existing code files

2. **Delegate to sub-agent**:
   ```
   Task(
     subagent_type: "general-purpose",
     model: "sonnet",  // Use "opus" if task involves logic/algorithms
     prompt: "Implement [requirement] per §X.Y.

     Spec requirement (§X.Y):
     [quoted spec text]

     Files to modify:
     - path/to/file.py

     Expected changes:
     - [describe expected implementation]"
   )
   ```

3. **After sub-agent completes** (main conversation):
   - Review the changes made
   - If issues found, fix with `Task` using `model: "opus"`
   - Update the tracker with implementation notes
   - Update task status

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

### Implementation via Sub-Agents

For each task, use the sub-agent delegation pattern to preserve main conversation context:

#### Step 1: Prepare Context (Main Conversation)

**CRITICAL**: Before delegating any task:

1. Read the tracker file to get the section references
2. **Re-read the relevant section(s) from the original spec document**
3. Note any specific requirements, formats, or constraints mentioned
4. Identify relevant existing code files the sub-agent will need

This prevents drift by ensuring you're always working from the source of truth.

#### Step 2: Delegate to Sub-Agent

Spawn a sub-agent for the implementation work:

```
Task(
  subagent_type: "general-purpose",
  model: "sonnet",  // Use "haiku" for simpler tasks
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

#### Step 3: Review and Verify (Main Conversation)

After sub-agent completes:

1. Review the changes made by the sub-agent
2. Verify they match the spec requirements
3. If issues found:
   - For minor fixes: fix directly
   - For complex issues: spawn another sub-agent with `model: "opus"`

#### Step 4: Update Tracker

1. Update the tracker file:
   - Change status from `pending` to `complete` or `partial`
   - Add implementation notes with file:line references
   - Add entry to Implementation Log

2. Update the task status using TaskUpdate

Example tracker update:
```markdown
| §2.4 | Detect merged tickets | complete | EdgeCaseHandler.check_merge() at src/handlers.py:156 |
```

### Handling Sub-Agent Issues

If a sub-agent's implementation has gaps or errors:

1. Note the specific issue
2. Spawn a fix sub-agent with Opus for complex reasoning:
   ```
   Task(
     subagent_type: "general-purpose",
     model: "opus",
     prompt: "Fix implementation issue in [file].

     ## Problem
     [Describe the gap or error]

     ## Spec Requirement (§X.Y)
     [Quote the spec]

     ## Current Implementation
     [What exists now at file:line]

     ## Expected Fix
     [What needs to change]"
   )
   ```

---

## Phase 3: Verification (`/implement verify [spec-name]`)

When the user requests verification:

**Important**: Verification requires careful reasoning to catch subtle gaps. Use `model: "opus"` when delegating verification work to sub-agents.

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

**Optional optimization**: For large specs, delegate section verification to parallel sub-agents:

```
Task(
  subagent_type: "general-purpose",
  model: "opus",  // Use Opus for verification - catches subtle gaps
  prompt: "Verify implementation of §X against the specification.

  ## Spec Section (§X)
  [Quote the full section]

  ## Claimed Implementation
  [From tracker: file:line references]

  ## Task
  1. Read each claimed implementation file
  2. Verify the code matches EVERY requirement in the spec section
  3. Report: Complete / Partial (what's missing) / Gap (not implemented)

  Be thorough - check edge cases, error handling, and exact formats."
)
```

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

### Step 4: Fix Verification Failures

When verification identifies gaps or issues, **always use Opus** to fix them:

1. **For each gap**, spawn a fix sub-agent:
   ```
   Task(
     subagent_type: "general-purpose",
     model: "opus",  // Always Opus for fixes
     prompt: "Fix verification gap in [file].

     ## Gap Details
     - **Spec section**: §X.Y
     - **Spec requirement**: [exact quote]
     - **Current state**: [what exists at file:line]
     - **What's missing**: [from gap analysis]

     ## Task
     1. Read the current implementation
     2. Understand why it doesn't meet the spec
     3. Implement the fix to fully satisfy §X.Y
     4. Summarize what you changed"
   )
   ```

2. **After each fix**, re-verify that specific section

3. **Update the tracker** with new implementation notes

4. **Repeat** until all gaps are resolved

**Why always Opus for fixes?** Verification failures often involve subtle misunderstandings of requirements or edge cases. Opus's stronger reasoning catches these nuances and produces correct fixes the first time.

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

## Recovery After Compaction

Context compaction can cause Claude to lose detailed instructions. This section helps you recognize and recover from compaction.

### Signs That Compaction Has Occurred

You may have experienced compaction if:
- You don't remember the specific spec sections you were implementing
- You're unsure what `/implement` means or how to use it
- The conversation feels like it's starting fresh mid-task
- You have a vague sense of "implementing something" but lack specifics

### Recovery Steps

If you suspect compaction has occurred:

1. **Check for tracker files**: Look for `.impl-tracker-*.md` in the current directory
   ```
   Glob(".impl-tracker-*.md")
   ```

2. **Read the tracker**: The tracker contains recovery instructions and current state

3. **Read the spec**: The tracker's `**Specification**:` line points to the source document

4. **Check TaskList**: See what tasks exist and their status

5. **Resume work**: Use the tracker's Requirements Matrix to understand what's done and what's pending

### Self-Recovery Protocol

When you read a tracker file, look for the `## Recovery Instructions` section. Follow those instructions - they're designed to work even if you've lost all other context about the implementation skill.

**Key workflow after recovery**: Tracker → Spec sections → Sub-agent → Verify → Update tracker

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
