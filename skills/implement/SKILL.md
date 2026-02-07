---
name: implement
description: Use this skill when implementing features from a specification document, business process document, or requirements document. Also use this skill when the user mentions .impl-tracker files, asks to fix implementation gaps, wants to verify implementation against a spec, or wants to continue/resume an in-progress implementation. Helps maintain connection to the source document throughout implementation and provides systematic verification.
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

### Pre-Implementation Check

**Before writing any implementation code**, verify:
1. A tracker file (`.impl-tracker-*.md`) exists in the current directory
2. The tracker has a populated Requirements Matrix
3. Tasks have been created via TaskCreate

If any of these are missing, STOP and complete Phase 1 first. Do not proceed to implementation without a tracker, even if you have the spec content in context.

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

After the implementation sub-agent completes:

1. Review the changes made by the sub-agent
2. Verify they match the spec requirements
3. **Run existing tests** to check for regressions:
   - Run the full test suite or at minimum the relevant test files
   - If tests fail, fix the issues before proceeding
4. If issues found:
   - For minor fixes: fix directly
   - For complex issues: spawn another sub-agent with `model: "opus"`
   - **Re-run tests after any fix**

#### Step 4: Write Tests for New Functionality

After the implementation is reviewed and existing tests pass, determine what tests are needed for the new code. This is a separate step from implementation — do not bundle test writing into the implementation sub-agent.

**Determine what to test** by re-reading the spec sections for this task and examining what was implemented. Focus on meaningful, spec-driven tests:

- **Does this endpoint/view exist and respond correctly?**
- **Do permissions and access controls work as specified?**
- **Does this algorithm/logic produce correct results for spec-defined scenarios?**
- **Do error cases behave as the spec requires?**

Do NOT write trivial tests (testing that a constant equals itself, testing framework boilerplate, testing Python's built-in behavior). Every test should verify a requirement or behavior from the spec.

**If the spec doesn't clearly define expected behavior for a piece of functionality, and you can't reasonably infer it from context, ask the user** what the expected behavior should be before writing tests.

**Delegate test writing to a sub-agent:**

```
Task(
  subagent_type: "general-purpose",
  model: "sonnet",  // Use "opus" for complex logic or algorithm tests
  prompt: "Write tests for the implementation of §X.Y.

  ## Spec Requirement (§X.Y)
  [Quote the spec text - this defines WHAT to test]

  ## Implementation
  [List files and key functions/classes that were implemented]

  ## Test Expectations
  - [Specific behaviors to verify, derived from the spec]

  ## Existing Test Patterns
  [Show an example from the existing test suite so tests match project conventions]

  ## Guidelines
  - Each test should verify a specific spec requirement or behavior
  - Do not write trivial or boilerplate tests
  - Include edge cases mentioned in the spec
  - Use descriptive test names that reference the requirement"
)
```

After the test sub-agent completes, **run the full test suite** to confirm both new and existing tests pass.

#### Step 5: Update Tracker

**Only update to `complete` after implementation is verified AND tests pass.**

1. Update the tracker file:
   - Change status from `pending` to `complete` or `partial`
   - Add implementation notes with file:line references
   - Add test file references (required — not optional)
   - Add entry to Implementation Log

2. Update the task status using TaskUpdate

Example tracker update:
```markdown
| §2.4 | Detect merged tickets | complete | EdgeCaseHandler.check_merge() at src/handlers.py:156 | test_handlers.py:45 |
```

**Do not mark as `complete` if:**
- Tests are failing
- You haven't run the tests
- New functionality has no tests
- There are linting/type errors

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

### Step 0: Run Tests and Validate Code

**Before any spec verification, ensure the code actually works:**

1. **Run the test suite** (if one exists):
   - Run all tests: `pytest`, `npm test`, `cargo test`, etc.
   - If tests fail, fix them BEFORE proceeding with spec verification
   - Document test coverage gaps in the tracker

2. **Run linting/type checking** (if configured):
   - Python: `mypy`, `flake8`, `black --check`
   - TypeScript: `tsc --noEmit`, `eslint`
   - Other languages: run their standard linters
   - Fix any errors before proceeding

3. **Verify the code compiles/runs**:
   - For compiled languages: ensure it builds without errors
   - For interpreted languages: do a basic import/load check
   - For web apps: verify the dev server starts

**If any of these fail, you are NOT ready for verification.** Fix the issues first.

This catches field name typos, import errors, type mismatches, and other mechanical issues that spec verification alone won't find.

### Finding the Right Tracker

1. If spec-name provided: Look for `.impl-tracker-<spec-name>.md`
2. If not provided: List all `.impl-tracker-*.md` files in current directory
   - If exactly one: use it
   - If multiple: show list and ask which one
   - If none: inform user no active implementations found

### Step 1: Build the Verification Plan (Main Conversation)

Read ONLY these files in the main conversation:
1. The implementation tracker (`.impl-tracker-<name>.md`) — to understand spec structure and file references
2. The spec document's **structure/table of contents only** — to know which sections exist
3. **Check for previous verification reports**: `Glob("verify-*.md")` in the project directory — if one or more exist, read the **most recent** report. This triggers **re-verification mode** (see below)

**Do NOT read full spec sections or implementation files in the main conversation.** Build a plan:
- List each spec section, its location, and what it covers
- Identify the implementation files each section maps to (from tracker)
- If re-verifying: extract the list of open V-items from the previous report

### Step 2: Extract Individual Requirements (Main Conversation)

Read each spec section and extract its **individual requirements** — the specific MUST/SHOULD/COULD statements or concrete behavioural expectations, not the section headings. This is a lightweight step — you're building a requirement list, not analysing code.

**Key distinction**: A spec subsection like "§2.1 Quick Capture" is a *topic area*, not a single requirement. It typically contains multiple individual requirements like "The system MUST allow adding assets by scanning a barcode", "The system SHOULD pre-fill fields from barcode data", etc. Each of those is a requirement. That's the level of granularity you need.

For each section:
1. Read the section content
2. Extract each individual requirement with its §N.M reference and a one-line summary
3. Note any implementation hints from the tracker (file:line references)
4. Release the section content from context — you only need the requirement list going forward

Build a flat list of all requirements to verify:

```
§2.1.1 — Quick capture: scan barcode to add asset — impl hint: views/capture.py:30
§2.1.2 — Quick capture: pre-fill fields from barcode data — impl hint: views/capture.py:55
§2.1.3 — Quick capture: manual entry fallback — no hint
§2.2.1 — Asset detail view shows all fields — impl hint: views/assets.py:80
§2.2.2 — Asset edit with field validation — impl hint: views/assets.py:120
§2.3.1 — Checkout assigns asset to borrower — impl hint: views/checkout.py:15
...
```

A typical spec section (like §2 Functional Requirements with 15 subsections) should produce **30-60+ individual requirements**, NOT 15.

### Step 3: Requirement-Level Verification via Sub-Agents (Parallel)

**Each sub-agent verifies ONE requirement.** This is not a guideline — it is a hard rule.

```python
# Pattern: ONE requirement = ONE sub-agent

# 1. Extract the single requirement text (from Step 2)
req_text = "§2.1.1: The system MUST allow adding assets by scanning a barcode. The scanned code MUST be validated against known formats."

# 2. Build implementation hints from tracker (if available)
impl_hints = "Implementation tracker references: views/capture.py:30"

# 3. Delegate — one requirement, one agent
Task(
  subagent_type: "general-purpose",
  model: "opus",
  prompt: """Verify implementation of ONE spec requirement against the codebase.

## Requirement: §2.1.1 — Quick Capture: Scan Barcode to Add Asset

<paste the single requirement text — NOT the whole §2.1 subsection>

## Implementation Search Instructions

Search directory: <implementation_dir>
Implementation hints (from tracker): <impl_hints>

1. Search the codebase for code that implements this requirement (use Grep/Glob to find relevant files)
2. Read the implementation files to confirm they satisfy the requirement
3. Search for test files covering this implementation (look in tests/, test_*, *_test.py, etc.)
4. Assess test coverage: what's tested, what's missing

## Report Format (use ONLY this format)

### §2.1.1 — Quick Capture: Scan Barcode

**Spec says**: <exact quote or summary of the requirement>
**Status**: Implemented / Partial / Not Implemented / N/A
**Implementation**: `file.py:123` — <brief description of how it's implemented>
**Test coverage**: Full / Partial / None
**Tests**: `test_file.py:45` — <what's tested>
**Missing tests**: <what's not tested — edge cases, error paths, permission boundaries, etc.>

(The V<N> ID will be assigned by the main conversation when assembling the report.
Use the §N.M reference as-is — the main conversation handles V-item numbering.)

Keep your response focused on findings only. Do NOT suggest fixes or implementation code.
Do NOT restate the spec beyond the brief quote. Be specific with file:line references.
"""
)
```

**HARD RULE: One requirement per sub-agent.** Do NOT batch multiple requirements into one agent. Do NOT group by subsection. Do NOT cluster "related" requirements.

The only exception: if two requirements are literally about the same line of code (e.g., "field MUST be required" and "field MUST be validated as email"), you MAY put those two in one agent. Never more than 2, and only when they test the exact same code path.

**Anti-pattern — DO NOT do this:**
```
Agent 1: §2.1 (Quick Capture), §2.2 (Asset Management), §2.3 (Checkout), §2.4 (Barcodes)
Agent 2: §2.5 (NFC), §2.6 (Search), §2.7 (Stocktake), §2.8 (Bulk Ops), §2.9 (Exports)
```
This groups entire subsections (each containing multiple requirements) into a single agent. The agent will rush through them, miss details, and produce shallow findings. This is the section-level batching pattern and it defeats the purpose of per-requirement verification.

**Correct pattern:**
```
Agent 1:  §2.1.1 — Scan barcode to add asset
Agent 2:  §2.1.2 — Pre-fill fields from barcode data
Agent 3:  §2.1.3 — Manual entry fallback
Agent 4:  §2.2.1 — Asset detail view
Agent 5:  §2.2.2 — Asset edit with validation
Agent 6:  §2.3.1 — Checkout assigns to borrower
Agent 7:  §2.3.2 — Checkin returns asset
...
Agent 35: §8.1.1 — Unit test coverage target
```

Yes, this means 20-40+ parallel agents for a medium-sized spec. That's correct. Each agent runs fast (one focused search), produces precise results, and finishes quickly. The total wall-clock time is often *less* than the batched approach because agents aren't serialising through a long list of requirements internally.

### Step 4: Assemble Verification Report (Main Conversation)

Collect findings from sub-agents and write them directly to a report file. Do NOT accumulate all results in conversation context — write incrementally.

Create the report at `verify-<spec-name>-<date>.md` in the project directory.

Each finding gets a **V-item ID** (`V1`, `V2`, ...) that persists across verification runs. V-item IDs are assigned sequentially during report assembly. On re-verification, resolved items keep their original ID for traceability.

```markdown
# Implementation Verification: <Spec Name>

**Spec**: <path to spec>
**Implementation**: <path to implementation directory>
**Date**: <date>
**Previous Verification**: <path to previous report, or "None — initial verification">
**Run**: <N> (1 for initial, 2+ for re-verification)

## Summary

<2-3 sentence assessment of overall implementation completeness and test coverage>

**Overall Implementation Status**: X of Y requirements verified
**Test Coverage**: X of Y testable requirements have tests

## Requirement-by-Requirement Verification

### V1 — §N.M — <Requirement Title>

**Spec says**: <exact quote>
**Status**: Implemented / Partial / Not Implemented / N/A
**Implementation**: `file.py:123` — <brief description>
**Test coverage**: Full / Partial / None
**Tests**: `test_file.py:45` — <what's tested>
**Missing tests**: <what's not tested — edge cases, error paths, etc.>

### V2 — §N.M+1 — ...

## Test Coverage Summary

| V-Item | Section | Requirement | Impl Status | Test Coverage | Missing Tests |
|--------|---------|-------------|-------------|---------------|---------------|
| V1 | §2.1 | User login | Implemented | Partial | No test for locked account |
| V2 | §2.2 | Password reset | Implemented | Full | — |
| V3 | §2.3 | Session timeout | Not Implemented | None | All |

## Items Requiring Tests

Priority list of untested or under-tested requirements:

1. [HIGH] V3 — §X.Y — <requirement> — No tests at all, covers permission boundary
2. [MEDIUM] V1 — §A.B — <requirement> — Happy path tested, missing edge cases: <list>
3. [LOW] V5 — §C.D — <requirement> — Minor gap: <detail>

## Scorecard

| Metric | Score |
|--------|-------|
| Requirements Implemented | X / Y (Z%) |
| Fully Tested | A / B (C%) |
| Partially Tested | D |
| No Tests | E |
| Critical Gaps | F |

## Priority Gaps

1. [HIGH] V<N> — §X.Y — <description>
2. [MEDIUM] V<N> — §A.B — <description>

## Recommendations

1. **Must add tests for**: <list critical untested items>
2. **Implementation gaps**: <list unimplemented requirements>
3. **Partial implementations**: <list items needing completion>
```

### Step 5: Fix Verification Failures

When verification identifies gaps or issues, **always use Opus** to fix them:

1. **For each gap**, spawn a fix sub-agent with the V-item details:
   ```
   Task(
     subagent_type: "general-purpose",
     model: "opus",  // Always Opus for fixes
     prompt: "Fix verification gap identified as V<N>.

     ## V-Item Details
     - **V-item**: V<N> — §X.Y — <requirement title>
     - **Spec requirement**: [exact quote]
     - **Current state**: [what exists at file:line]
     - **What's missing**: [from verification report]

     ## Task
     1. Read the current implementation
     2. Understand why it doesn't meet the spec
     3. Implement the fix to fully satisfy §X.Y
     4. Summarize what you changed"
   )
   ```

2. **After each fix**, re-verify that specific requirement (single sub-agent, same pattern as Step 3)

3. **Update the tracker** with new implementation notes

4. **Repeat** until all gaps are resolved

5. **Re-run tests after fixes**: Every fix must be validated by running tests again. Never claim verification is complete until tests pass.

**Why always Opus for fixes?** Verification failures often involve subtle misunderstandings of requirements or edge cases. Opus's stronger reasoning catches these nuances and produces correct fixes the first time.

### Re-Verification Mode

When a previous verification report exists (`verify-<spec-name>-*.md`), the verify command runs in **re-verification mode**. Before starting, ask the user which mode they want:

> I found a previous verification report (`verify-<date>.md`) with X open V-items.
>
> How would you like to proceed?
> 1. **Re-verify from where we left off** — Check only the open V-items from the previous run, plus spot-check for regressions (faster, cheaper)
> 2. **Full re-verification from scratch** — Re-audit all spec requirements as if this were a fresh run, but carry forward V-item IDs for traceability

#### How Re-Verification Differs from Initial Verification

| Aspect | Initial Verification | Re-verify (from left off) | Re-verify (from scratch) |
|--------|---------------------|--------------------------|-------------------------|
| Scope | All spec requirements | Open V-items + spot-check | All requirements again |
| V-item IDs | Assigned fresh (V1, V2, ...) | Carried forward | Carried forward |
| Report structure | Full report | Delta report with resolution status | Full report with resolution status |
| Token cost | Full | ~30-50% of initial | ~100% of initial |

#### Re-Verification from Where We Left Off

1. **Read the most recent verification report** in the main conversation. Extract:
   - All V-items and their status (focus on those NOT fully implemented or NOT fully tested)
   - The V-item ID counter (so new items continue the sequence)

2. **Categorize previous V-items**:
   - **Open**: Status was Partial / Not Implemented, or test coverage was Partial / None — these MUST be re-checked
   - **Passed**: Status was Implemented AND test coverage was Full — these get a lightweight spot-check

3. **Dispatch re-verification sub-agents** (parallel):

   For each **open** V-item, spawn a sub-agent with the original finding AND the spec requirement:

   ```
   Task(
     subagent_type: "general-purpose",
     model: "opus",
     prompt: """Re-verify a previously identified issue.

   ## Previous Finding

   V12 — §3.2 — AI Thumbnail Generation
   **Previous status**: Partial
   **Previous issue**: Uses full URL instead of relative path for thumbnail src
   **Previous implementation**: templates/library/book_detail.html:45

   ## Spec Requirement

   <paste the spec requirement text>

   ## Instructions

   1. Read the implementation file(s) referenced in the previous finding
   2. Check if the specific issue has been addressed
   3. Search for the current implementation if the file/line has changed
   4. Re-assess test coverage for this requirement

   ## Report Format

   ### V12 — §3.2 — AI Thumbnail Generation

   **Previous status**: Partial
   **Current status**: Implemented / Partial / Not Implemented
   **Resolution**: FIXED / PARTIALLY FIXED / NOT FIXED
   **What changed**: <describe what was fixed, or why it's still open>
   **Implementation**: `file.py:123` — <current implementation>
   **Test coverage**: Full / Partial / None
   **Tests**: `test_file.py:45` — <what's tested>
   **Missing tests**: <what's still not tested>
   """
   )
   ```

   For **passed** V-items, do a lightweight spot-check: cluster 5-10 passed items into a single sub-agent that confirms the implementations still exist and haven't regressed. This is a sanity check, not a deep re-audit.

4. **Check for new requirements**: If the spec has been updated since the last verification, also run initial verification on any NEW requirements not covered by previous V-items. Assign new V-item IDs continuing from the previous counter.

#### Re-Verification from Scratch

Run the full initial verification flow (Steps 2-4 above), but:
- Read the previous report first to get the V-item ID assignments
- Match new findings to previous V-items by §N.M section reference
- Reuse existing V-item IDs where the same requirement is being verified
- Assign new IDs only for requirements that weren't in the previous report
- Include resolution status for items that were previously flagged

#### V-Item Lifecycle

V-items follow this lifecycle across verification runs:

```
Initial verification → V1 created (status: Partial)
Re-verification 1   → V1 checked (resolution: PARTIALLY FIXED)
Re-verification 2   → V1 checked (resolution: FIXED) — item closed
```

- **FIXED**: The issue is fully resolved. Appears in "Previous V-Item Resolution" but not in "Still Open"
- **PARTIALLY FIXED**: Progress was made but the issue isn't fully resolved. Describe what changed and what remains
- **NOT FIXED**: No meaningful progress on this item
- **REGRESSED**: A previously FIXED item has broken again (rare but important to flag)

V-item IDs are **permanent** — once V12 is assigned to "§3.2 AI Thumbnail Generation", it stays V12 forever, even across many re-verification runs. New issues discovered during re-verification get the next available ID.

### Context Efficiency Rules

Follow these rules strictly to avoid token waste:

1. **Main conversation reads ONLY the tracker and spec structure** — do NOT load full spec sections or implementation files into main context
2. **Pass spec requirement text directly in sub-agent prompts** — extract the text and embed it
3. **Sub-agents DO read implementation files** — they need to search the codebase to verify
4. **Cap sub-agent output** — structured findings only, no verbose analysis or code suggestions
5. **One requirement per sub-agent** — don't overload agents with entire sections
6. **Write findings directly to the report file** — don't accumulate results in main conversation context

### Definition of Done

Implementation is ONLY complete when ALL of these are true:

- [ ] **Tests pass**: All tests in the test suite pass (`pytest`, `npm test`, etc.)
- [ ] **No lint/type errors**: Code passes linting and type checking if configured
- [ ] **Code runs**: The application starts/compiles without errors
- [ ] **Spec verification complete**: All requirements are implemented or documented as N/A
- [ ] **Tracker updated**: Requirements matrix reflects final state with file:line references
- [ ] **Gaps documented**: Any remaining gaps are documented with severity and rationale

**Never claim "done" or "complete" without running tests first.** Field name typos, missing imports, type errors, and similar issues are embarrassing failures that testing catches. If no test suite exists, at minimum:
- Import/load the main modules to check for syntax errors
- Run any available linting tools
- Manually verify critical paths work

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

**Key workflow after recovery**: Tracker → Spec sections → Sub-agent → **Run tests** → Verify → Update tracker

**CRITICAL**: Never claim completion without running tests. Field name errors, import mistakes, and type mismatches won't be caught by spec verification alone.

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

## Critical Rule: No Implementation Without a Tracker

**NEVER begin implementing code without first creating a tracker file.** This is the most important rule of this skill. If you find yourself about to write implementation code and no `.impl-tracker-*.md` file exists, STOP and go through Phase 1 first.

This is especially important when the spec content is already visible in conversation context (e.g., after using `/spec` to create it). Having the spec in context makes it tempting to skip the tracker — but the tracker is what prevents gaps during context compaction. Without it, requirements WILL be missed.

## Implicit Activation

This skill may be activated not just by `/implement` but also when the user's message mentions tracker files, implementation gaps, or spec verification without explicitly invoking the command. In these cases:

1. **Do not silently take over.** Instead, ask the user if they'd like to use the implementation skill to handle their request. For example:
   > "It looks like you're working with an implementation tracker. Would you like me to use the `/implement` skill to systematically work through the gaps? This will re-read the spec, verify each gap against the source requirements, and fix them with proper tracking."
2. If the user agrees, proceed by reading the tracker to determine the appropriate phase (typically `continue` or `verify`).
3. If the user declines, assist them normally without the skill's workflow.

## Arguments Handling

The `$ARGUMENTS` variable contains what the user passed after `/implement`.

Parse it as follows:
- If it's a file path (contains `/` or ends in `.md`): Start planning phase
- If it starts with `status`: Show status (optional spec-name follows)
- If it starts with `verify`: Run verification (optional spec-name follows)
- If it starts with `continue`: Resume work (optional spec-name follows)
- If it's `list`: List all `.impl-tracker-*.md` files with their spec paths and status summaries
- If empty: Follow the **empty arguments procedure** below

### Empty Arguments Procedure

When `$ARGUMENTS` is empty:

1. Check for existing trackers (`.impl-tracker-*.md` in current directory)
   - If exactly one exists: offer to continue implementation
   - If multiple exist: show list and ask which to continue
2. If no trackers exist:
   - Search for recently-created spec/requirements documents: `Glob("**/*spec*.md")` and `Glob("**/*requirements*.md")`
   - If candidate specs are found: present them to the user and ask which to implement
   - If no candidates found: ask the user for the path to their specification document
3. **Once a spec path is identified, ALWAYS go through Phase 1 (Planning) to create the tracker before any implementation work begins.** Do not skip this step even if the spec content is already visible in the conversation.

### Tracker Discovery

To find trackers, glob for `.impl-tracker-*.md` in the current directory. Each tracker contains a `**Specification**:` line that points back to the original spec file.

Arguments: $ARGUMENTS
