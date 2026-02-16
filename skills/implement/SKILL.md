---
name: implement
description: Use this skill when implementing features from a specification document, business process document, or requirements document. Also use this skill when the user mentions .impl-tracker files, asks to fix implementation gaps, wants to verify implementation against a spec, or wants to continue/resume an in-progress implementation. Helps maintain connection to the source document throughout implementation and provides systematic verification.
argument-hint: <spec-path> | status [name] | verify [name] | continue [name] | list | config [setting] [value]
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
| `/implement config [setting] [value]` | View or update implementation preferences |

**Note**: `[spec-name]` is optional. If omitted and multiple trackers exist, you'll be prompted to choose. The spec-name is the basename without path or extension (e.g., for `docs/billing-spec.md`, use `billing-spec`).

## Preferences

Implementation preferences control workflow behavior across sessions and projects. Preferences are stored in simple markdown files.

### Preference Files

| File | Scope |
|------|-------|
| `.impl-preferences.md` (project directory) | Project-level — overrides global |
| `~/.claude/.impl-preferences.md` | Global default — applies to all projects |

**Lookup order**: Project file → Global file → Built-in defaults

### Preference File Format

```markdown
# Implementation Preferences

## Workflow
- **tdd-mode**: on
```

### Available Preferences

| Preference | Values | Default | Description |
|------------|--------|---------|-------------|
| `tdd-mode` | `on`, `off`, `ask` | `on` | Controls whether Test-Driven Development workflow is used |

- `on` — Always use the TDD workflow (write tests first, then implement)
- `off` — Always use the standard workflow (implement first, then write tests)
- `ask` — Prompt during Phase 1 planning so the user can choose per-implementation

### `/implement config` Subcommand

View or update preferences:

| Command | Description |
|---------|-------------|
| `/implement config` | Show current effective preferences (project + global + defaults) |
| `/implement config tdd on\|off\|ask` | Set TDD preference at project level |
| `/implement config --global tdd on\|off\|ask` | Set TDD preference as global default |

When setting a preference:
1. Read the existing preferences file (or create it if it doesn't exist)
2. Update the specified value
3. Write the file back
4. Confirm the change to the user, showing the effective preference chain

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

### Size-Based Routing for Large Specs

When a spec has breakout section files (e.g., produced by `/spec`), build a structural index before delegating work:

1. **Build the index**: Run `wc -c` on each section file. Estimate tokens: `estimated_tokens ≈ file_size_bytes / 4`
2. **Route by section size**:

| Section Size | Model | Grouping |
|-------------|-------|----------|
| < 5k tokens | `sonnet` | Group 2-3 sections per agent |
| 5k–20k tokens | `sonnet` | 1 section per agent |
| > 20k tokens | `opus` | 1 section per agent |

3. **Digest-based complexity escalation**: Instead of self-escalation, sonnet agents produce a DIGEST (5-10 lines) at the end of their response summarizing key entities, patterns, and complexity encountered. The main conversation checks the DIGEST against the complexity category table to determine if opus review is needed:

   | Category | DIGEST signals | Why opus review needed |
   |----------|---------------|----------------------|
   | Algorithms | "algorithm", "calculation", "formula", "heuristic" | Subtle correctness |
   | State machines | "state machine", "state transition", "lifecycle" | Complex interactions |
   | Permission/auth | "permission", "role inheritance", "RBAC", "access control" | Security boundaries |
   | Complex business rules | "conditional", "override", "exception", "cascading" | Edge cases |
   | Cross-cutting | "affects all", "global constraint", "system-wide" | Holistic view |

   Escalation is **MANDATORY** when a DIGEST matches any category — it is not discretionary. When matched: dispatch opus to REVIEW sonnet's code changes with focus on the flagged area. Do NOT rationalize skipping the review ("it looks fine", "the tests pass") — the whole point is that these categories have subtle failure modes that tests alone don't catch.

**Sub-split sections**: When a section was split into sub-files (e.g., `02a-`, `02b-`, `02c-`), each sub-file routes independently by its own size. Tasks referencing the parent section (e.g., §2) should include all sub-file paths in the sub-agent prompt.

**Note**: This only applies when the spec has breakout section files. Single-file specs use the standard model selection table above.

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
   - Sub-agent output comes via `TaskOutput` — use that directly
   - **Do NOT read or grep agent output files** — they are raw JSON transcripts, not usable text
   - Review the changes made
   - If issues found, fix with `Task` using `model: "opus"`
   - Update the tracker with implementation notes
   - Update task status

---

## Phase 1: Planning (`/implement <spec-path>`)

When the user provides a spec path, follow these steps:

### Step 1: Read and Parse the Specification

**STRUCT awareness check**: Before parsing the spec, look for `.spec-tracker-*.md` files in the spec's directory. If found, check for a `## Pending Structural Changes` section. If pending structural issues exist, warn the user:

> The spec has pending structural changes flagged by the `/spec` skill. These may affect implementation planning. Would you like to proceed anyway, or wait for the spec author to resolve them?

If the user chooses to proceed, note the pending issues in the tracker's Implementation Log.

**Detect spec type**: Check whether the spec has breakout section files. Look for `<!-- EXPANDED:` markers in the master document or a `sections/` directory alongside it. This determines the parsing approach:

#### Single-File Specs (no breakout sections)

1. Read the entire specification document
2. Identify the document's section structure (look for patterns like `## Section N`, `### N.M`, `§N.M`, numbered headings)
3. Extract each discrete requirement with its section reference

#### Multi-File Specs (breakout sections, e.g., from `/spec`)

Do NOT read all section files into main context — this will blow out the context window for large specs. Instead, build a structural index:

1. Read the master spec's **document map / table of contents only** — this gives you the full spec outline without loading section prose
2. Run `wc -c` on all section files to build the structural index:
   ```
   Bash("wc -c path/to/sections/*.md")
   ```
   Record each file's byte count and compute `estimated_tokens ≈ bytes / 4`
   - **Sub-file splitting**: Section files may use letter suffixes when a section was too large and got split (e.g., `02a-core-model.md`, `02b-core-relations.md`, `02c-core-validation.md`). The glob `sections/*.md` captures these automatically. Group sub-files under their parent section number — a task referencing §2 may need all `02*` sub-files.
   - **Routing**: Sub-split sections route independently by their own size. A task referencing a parent section should include all sub-file paths in the sub-agent prompt.
3. Read only the **section headings and requirement identifiers** (MUST/SHOULD/COULD statements) from each section file — don't read full section prose into main context
4. Sub-agents will read full section files themselves during Phase 2
5. **Store the structural index in the tracker** as the spec baseline (see `## Structural Index` in the tracker template). This enables spec evolution detection when resuming work across sessions.

Record the spec type in the tracker (`**Spec Type**: single-file` or `**Spec Type**: multi-file`) so that `/implement continue` knows which approach to use.

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
**TDD Mode**: <set in Step 5 after plan approval — on or off>
**Spec Type**: <single-file or multi-file — set in Step 1 based on spec structure>
**Spec Baseline**: <date — when structural index was captured>

## Structural Index

<!-- STRUCTURAL_INDEX
file: <path> | bytes: <N> | tokens: <N> | route: <model> | parent: §<N>
...
-->

| File | Bytes | Est. Tokens | Model Route | Parent Section |
|------|-------|-------------|-------------|----------------|
| ... | ... | ... | ... | ... |

**Baseline captured**: <date>

*Only populated for multi-file specs. For single-file specs, delete this section.*

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

### Step 4: Determine TDD Mode

Before presenting the plan, determine which implementation workflow to use:

1. **Read the TDD preference** using the lookup chain:
   - Check for `.impl-preferences.md` in the project directory
   - If not found (or no `tdd-mode` set), check `~/.claude/.impl-preferences.md`
   - If neither exists, use the built-in default: `on`

2. **If the preference is `on` or `off`**, record it — no user prompt needed.

3. **If the preference is `ask`**, you will present the choice as part of the plan presentation in Step 5.

### Step 5: Present the Plan

Show the user:
1. A summary of the specification structure
2. The requirements matrix from the tracker
3. The proposed task breakdown
4. The proposed implementation workflow:
   - If TDD preference was `on` or `off`: state which workflow will be used
   - If TDD preference is `ask`: present the choice:

   > **Implementation workflow**: Which workflow would you like to use?
   >
   > - **TDD mode**: Tests are written first from the spec (before any implementation code), then implementation is done to make them pass. This catches spec drift early because the test-writing agent works purely from the spec with no implementation bias.
   > - **Standard mode**: Implementation is done first, then tests are written afterward to verify the implementation.

5. Any questions about ambiguous requirements or implementation approach

After the user approves the plan (and chooses a workflow if `ask` mode):
- **Record the choice in the tracker** by setting the `**TDD Mode**:` field to `on` or `off`. This ensures `/implement continue` knows which workflow to use even if the preference changes later.

---

## Phase 2: Implementation

**Workflow selection**: Check the tracker's `**TDD Mode**:` field to determine which workflow to use. If `on` or not set, use the **Phase 2 (TDD Mode): Test-First Implementation** workflow below instead of this standard workflow. If `off`, use this standard workflow. If the field is missing (e.g., tracker created before TDD mode existed), check preferences to determine the mode and update the tracker — default is `on`.

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
2. **Re-read the relevant section(s) from the original spec document** (for single-file specs) or **confirm which section file(s) the sub-agent will need to read** (for multi-file specs)
3. Note any specific requirements, formats, or constraints mentioned
4. Identify relevant existing code files the sub-agent will need

This prevents drift by ensuring you're always working from the source of truth.

#### Step 2: Delegate to Sub-Agent

Spawn a sub-agent for the implementation work. The prompt style depends on spec type:

**Single-file specs** — embed the spec text directly in the prompt:

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

**Multi-file specs (breakout sections)** — pass file paths instead of embedded content. The sub-agent reads the section file itself, keeping main conversation context lean:

```
Task(
  subagent_type: "general-purpose",
  model: "sonnet",  // Route by section size — see Size-Based Routing table
  prompt: "Implement [requirement] per §X.Y of the specification.

  ## Spec Layout (structural index)
  [Paste the structural index so the agent knows the full spec layout]

  ## Section to Read
  Read the spec section at: path/to/sections/section-X.md
  Focus on the requirements in §X.Y.

  ## Requirement References
  - §X.Y.1: [one-line summary from Phase 1 extraction]
  - §X.Y.2: [one-line summary]

  ## Files to Modify
  - path/to/file.py (describe what changes needed)

  ## Context
  [Any relevant existing code patterns or constraints]

  ## Expected Outcome
  - [Describe what the implementation should do]

  After implementation, summarize what you changed and any issues encountered.

  At the end of your response, include a DIGEST section:
  === DIGEST ===
  - Entities: <key classes, models, services touched>
  - Patterns: <design patterns used or encountered>
  - Complexity: <any algorithmic, state machine, auth, or business rule complexity>
  === END DIGEST ==="
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
5. **Check DIGEST for complexity escalation** (multi-file/sonnet agents only):
   - Extract the `=== DIGEST ===` section from the sub-agent's response
   - Check DIGEST signals against the complexity category table (see Size-Based Routing)
   - If any category matches: dispatch opus to review the sonnet's code changes with focus on the flagged complexity area
   - Run tests again after any opus-driven changes

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

## Phase 2 (TDD Mode): Test-First Implementation

This workflow runs **instead of** the standard Phase 2 when TDD mode is active (tracker shows `**TDD Mode**: on`). The key difference: tests are written first from the spec before any implementation exists, then implementation is done to make them pass.

### Why TDD Mode Works Well with Sub-Agents

- **Spec fidelity**: The test-writing agent reads only the spec — no implementation code exists to bias it
- **Clear acceptance criteria**: The implementation agent has concrete pass/fail signals from the tests
- **Drift detection**: If the implementation agent can't make tests pass, it reveals misunderstandings early
- **Different contexts catch different things**: Test and implementation agents interpret the spec independently — disagreements surface spec ambiguities
- **Regression safety**: Tests exist before code, so there's no "forgot to write tests" problem

### Pre-Implementation Check

Same as the standard workflow — verify the tracker exists with a populated Requirements Matrix and tasks have been created.

### TDD Implementation via Sub-Agents

For each task, follow this test-first cycle:

#### Step 1: Prepare Context (Main Conversation)

Same as the standard workflow:

1. Read the tracker file to get the section references
2. **Re-read the relevant section(s) from the original spec document** (for single-file specs) or **confirm which section file(s) the sub-agent will need to read** (for multi-file specs)
3. Note any specific requirements, formats, or constraints mentioned
4. Identify relevant existing code files and test conventions

#### Step 2: Write Tests First

Delegate test writing to a sub-agent working **purely from the spec**. The sub-agent should NOT see any implementation code — only the spec requirements and existing test patterns.

**For multi-file specs with breakout sections**: Pass the section file path instead of quoting the full text. The sub-agent reads the file directly. Include the structural index so the agent understands the full spec layout.

```
Task(
  subagent_type: "general-purpose",
  model: "sonnet",  // Use "opus" for complex logic or algorithm tests
  prompt: "Write tests for §X.Y BEFORE implementation exists.

  ## Spec Requirement (§X.Y)
  [Exact spec text — or for multi-file specs: 'Read the spec section at: path/to/sections/section-X.md']

  ## What to Test
  Write tests that verify the spec requirements are met.
  These tests SHOULD FAIL right now — that's expected and correct.

  ## Project Test Conventions
  [Show existing test patterns/framework setup from the project]

  ## Important
  - Write tests from the SPEC, not from any existing code
  - Tests should be specific enough to catch wrong implementations
  - Include edge cases mentioned in the spec
  - Each test should verify one clear spec requirement
  - Tests MUST be runnable (correct imports, fixtures, etc.)
  - Do NOT stub/mock the thing being tested — test real behavior
  - Use descriptive test names that reference the requirement

  At the end of your response, include a DIGEST section:
  === DIGEST ===
  - Entities: <key classes, models, services touched>
  - Patterns: <design patterns used or encountered>
  - Complexity: <any algorithmic, state machine, auth, or business rule complexity>
  === END DIGEST ==="
)
```

#### Step 3: Run Tests — Confirm Failures

Run the test suite. The new tests **should fail** (since implementation doesn't exist yet). This validates:
- Tests are checking something real (not trivially passing)
- Tests are syntactically valid and runnable
- Test infrastructure works

**If tests pass unexpectedly**: Investigate — either the feature already exists, or tests are too loose. Tighten the tests or confirm the feature is already implemented and skip to tracker update.

**If tests error (import/syntax)**: Fix the test setup (imports, fixtures, file paths), not the test assertions themselves. The assertions should remain as-is since they reflect the spec.

#### Step 4: Implement to Pass Tests

Delegate implementation to a sub-agent. **Key difference from the standard workflow**: include the test file path so the implementation agent knows the acceptance criteria.

**For multi-file specs with breakout sections**: Pass the section file path instead of quoting the full text. The sub-agent reads the file directly.

```
Task(
  subagent_type: "general-purpose",
  model: "sonnet",  // Use "opus" for complex logic or algorithms
  prompt: "Implement §X.Y to make the failing tests pass.

  ## Spec Requirement (§X.Y)
  [Exact spec text — or for multi-file specs: 'Read the spec section at: path/to/sections/section-X.md']

  ## Failing Tests
  Tests at [test_file:lines] define the acceptance criteria.
  Read them to understand what's expected.

  ## Files to Modify
  - path/to/file.py (describe what changes needed)

  ## Context
  [Any relevant existing code patterns or constraints]

  ## Important
  - Make the failing tests pass
  - Don't modify the tests
  - Also ensure existing tests still pass
  - Summarize what you changed and any issues encountered

  At the end of your response, include a DIGEST section:
  === DIGEST ===
  - Entities: <key classes, models, services touched>
  - Patterns: <design patterns used or encountered>
  - Complexity: <any algorithmic, state machine, auth, or business rule complexity>
  === END DIGEST ==="
)
```

#### Step 5a: Check DIGEST for Complexity Escalation

After the implementation sub-agent completes and before running tests:

1. Extract the `=== DIGEST ===` section from the sub-agent's response
2. Check DIGEST signals against the complexity category table (see Size-Based Routing)
3. If any category matches: dispatch opus to review the sonnet's code changes with focus on the flagged complexity area
4. Run tests after any opus-driven changes

This step only applies when the implementation sub-agent was a sonnet (multi-file routing). Skip for opus agents.

#### Step 5: Run Tests — Confirm Passes

Run the full test suite:
- **New tests should now pass** — this confirms the implementation meets the spec
- **Existing tests should still pass** — no regressions
- If new tests still fail: fix the implementation (not the tests), then re-run
- If a test seems genuinely wrong after seeing the implementation: **flag it for user review** rather than changing the test — the test was written from the spec, so a mismatch may indicate a spec ambiguity worth discussing
- If existing tests break: fix the regression in the implementation

#### Step 6: Update Tracker

Same as the standard workflow's Step 5:

1. Update the tracker file:
   - Change status from `pending` to `complete` or `partial`
   - Add implementation notes with file:line references
   - Add test file references
   - Add entry to Implementation Log

2. Update the task status using TaskUpdate

**Only mark as `complete` after both new and existing tests pass.**

### Handling Issues in TDD Mode

If the implementation sub-agent cannot make all tests pass:

1. Review the failing tests against the spec to confirm they're correct
2. If tests are correct: spawn a fix sub-agent with `model: "opus"` including both the spec text and the failing test output
3. If a test misinterprets the spec: flag it for user review before changing it
4. Never silently modify tests to match a wrong implementation

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
3. **Check for previous verification reports**: `Glob(".impl-verification/<spec-name>/verify-*.json")` in the project directory — if one or more exist, read the **most recent** report. This triggers **re-verification mode** (see below)

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

### Tools Setup

Before running verification sub-agents, resolve the tools directory:

```bash
REPO_DIR="$(dirname "$(readlink -f ~/.claude/skills/implement/SKILL.md)")/../.."
TOOLS_DIR="$REPO_DIR/tools"
PYTHON=python3
```

These variables are used in Steps 3-4 below.

### Step 3: Requirement-Level Verification via Sub-Agents (Parallel)

**Each sub-agent verifies ONE requirement.** This is not a guideline — it is a hard rule.

**Pre-flight**: Create the fragments directory and clear any stale markers:

```bash
mkdir -p .impl-verification/<spec-name>/fragments/ && rm -f .impl-verification/<spec-name>/fragments/*.done
```

```python
# Pattern: ONE requirement = ONE sub-agent

# 1. Extract the single requirement text (from Step 2)
req_text = "§2.1.1: The system MUST allow adding assets by scanning a barcode. The scanned code MUST be validated against known formats."

# 2. Build implementation hints from tracker (if available)
impl_hints = "Implementation tracker references: views/capture.py:30"

# 3. Delegate — one requirement, one agent (run_in_background: true)
Task(
  subagent_type: "general-purpose",
  model: "opus",
  run_in_background: true,  # MUST run in background — do NOT read TaskOutput
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

## Output — Write findings to disk as JSON

Write your findings to: .impl-verification/<spec-name>/fragments/02-01-01.json
(named by section number: §2.1.1 → 02-01-01.json)

Use this EXACT JSON format:
{
  "schema_version": "1.0.0",
  "fragment_id": "02-01-01",
  "section_ref": "§2.1.1",
  "title": "Quick Capture: Scan Barcode",
  "requirement_text": "<exact quote or summary of the requirement>",
  "moscow": "MUST",
  "status": "partial",
  "implementation": {
    "files": [{"path": "file.py", "lines": "30-45", "description": "brief desc"}],
    "notes": "optional notes"
  },
  "test_coverage": "partial",
  "tests": [{"path": "test_file.py", "lines": "10-25", "description": "what's tested"}],
  "missing_tests": ["specific missing test"],
  "missing_implementation": ["specific missing feature"],
  "notes": ""
}

Valid values:
- moscow: MUST, SHOULD, COULD, WONT
- status: implemented, partial, not_implemented, na
- test_coverage: full, partial, none

Keep findings focused. Do NOT suggest fixes or implementation code.
Do NOT restate the spec beyond the brief quote. Be specific with file:line references.

After writing the JSON file, write a completion marker:
.impl-verification/<spec-name>/fragments/02-01-01.done (contents: just "done").
The .done marker MUST be the last file you write.
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

### Step 4: Assemble Verification Report (Deterministic)

**Context protection**: Do NOT call `TaskOutput` on verification agents. With 20-40+ parallel agents, reading their output would fill the context window. Instead, wait for `.done` markers, then run the Python assembly tool.

**Wait for completion:**

```bash
"$PYTHON" "$TOOLS_DIR/wait_for_done.py" --dir .impl-verification/<spec-name>/fragments/ --count <number of requirements dispatched>
```

**Assemble the report:**

```bash
"$PYTHON" "$TOOLS_DIR/verify_report.py" \
  --fragments-dir .impl-verification/<spec-name>/fragments/ \
  --spec-path <spec-path> \
  --impl-path . \
  --project-name "<spec-name>" \
  --output .impl-verification/<spec-name>/verify-<date>.json
```

For re-verification, add `--previous` pointing to the previous report JSON:

```bash
"$PYTHON" "$TOOLS_DIR/verify_report.py" \
  --fragments-dir .impl-verification/<spec-name>/fragments/ \
  --spec-path <spec-path> \
  --impl-path . \
  --project-name "<spec-name>" \
  --output .impl-verification/<spec-name>/verify-<date>.json \
  --previous .impl-verification/<spec-name>/verify-<prev-date>.json
```

This produces:
- `.impl-verification/<spec-name>/verify-<date>.json` — machine-readable report (queryable with jq)
- `.impl-verification/<spec-name>/verify-<date>.md` — human-readable report

The tool deterministically handles:
- Fragment validation (hard errors on missing fields / invalid enums, soft warnings on contradictions)
- V-item ID assignment (sequential by fragment_id sort order for initial; section_ref matching for re-verification)
- Statistics: `implementation_rate = (implemented + partial × 0.5) / (total - na)`, same for test_rate
- Priority gap classification (high/medium/low by MoSCoW × status × test_coverage)
- Markdown rendering with all report sections (header, summary, requirement-by-requirement, test coverage table, gaps, scorecard, recommendations)

**The report format is defined in `tools/verification_schema.py:render_markdown()`.** Do not write report markdown manually — the tool handles it.

**Present to user:**

Read the `.md` report file (or just its Summary and Scorecard sections) and present results:

> **Verification complete.** See the full report at `.impl-verification/<spec-name>/verify-<date>.md`.
>
> **Results**: X of Y requirements implemented, A of B have test coverage.
> Implementation rate: Z%, Test rate: W%
>
> **Critical gaps** (if any):
> - <top 3 from priority_gaps with priority "high">
>
> **Next steps:**
> - Address implementation gaps (see Priority Gaps section)
> - Add missing tests (see Items Requiring Tests section)
> - Re-run `/implement verify` after fixes to track progress (V-item IDs are preserved across runs)

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

5. **Re-run tests after fixes**: Every fix must be validated by running tests again. Never claim verification is complete until tests pass. The updated report will be at `.impl-verification/<spec-name>/verify-<date>.md`.

**Why always Opus for fixes?** Verification failures often involve subtle misunderstandings of requirements or edge cases. Opus's stronger reasoning catches these nuances and produces correct fixes the first time.

### Re-Verification Mode

When a previous verification report exists (`.impl-verification/<spec-name>/verify-*.json`), the verify command runs in **re-verification mode**. Before starting, ask the user which mode they want:

> I found a previous verification report (`.impl-verification/<spec-name>/verify-<date>.md`) with X open V-items.
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

   ## Output — Write findings to disk as JSON

   Write your findings to: .impl-verification/<spec-name>/fragments/03-02.json

   Use this EXACT JSON format:
   {
     "schema_version": "1.0.0",
     "fragment_id": "03-02",
     "section_ref": "§3.2",
     "title": "AI Thumbnail Generation",
     "requirement_text": "<the spec requirement text>",
     "moscow": "MUST",
     "status": "implemented",
     "v_item_id": "V12",
     "previous_status": "partial",
     "resolution": "fixed",
     "implementation": {
       "files": [{"path": "file.py", "lines": "123", "description": "current implementation"}],
       "notes": ""
     },
     "test_coverage": "full",
     "tests": [{"path": "test_file.py", "lines": "45", "description": "what's tested"}],
     "missing_tests": [],
     "missing_implementation": [],
     "notes": "Describe what changed or why it's still open"
   }

   Valid resolution values: fixed, partially_fixed, not_fixed, regressed

   After writing the JSON, write a completion marker:
   .impl-verification/<spec-name>/fragments/03-02.done (contents: just "done").
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
6. **Do NOT call TaskOutput on verification agents** — wait for `.done` markers, then run `verify_report.py` for deterministic assembly

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
2. **Spec freshness check** — detect whether the spec has changed since the last session:
   - **Multi-file specs**: Re-run `wc -c path/to/sections/*.md` and compare against the stored Structural Index in the tracker:
     - **New files**: Files present on disk but not in the index (including new sub-splits like `02d-`)
     - **Removed files**: Files in the index but no longer on disk
     - **Size changes**: Any file whose byte count changed by >20% from the stored value
     - **Sub-split patterns**: A previously single file now has letter-suffix variants (e.g., `02.md` → `02a-`, `02b-`)
   - **Single-file specs**: Compare the file size (via `wc -c`) against the value stored in the tracker's `**Spec Baseline**` date — if the file's modification time is newer than the baseline date, flag it
   - **STRUCT check**: Look for `.spec-tracker-*.md` files (from the `/spec` skill) and check for a `## Pending Structural Changes` section — this indicates the spec author flagged structural issues that affect implementation
   - **When changes detected**: Present the user with 3 options (see **Spec Evolution Handling** below)
   - **When no changes detected**: Proceed silently
3. **Check the `**TDD Mode**:` field** — use the TDD workflow (Phase 2 TDD Mode) or standard workflow accordingly. If the field is missing (tracker created before TDD mode existed), check preferences to determine the mode and update the tracker.
4. Read the task list
5. Identify the next pending task
6. **Re-read the relevant spec sections** before continuing
7. Resume implementation using the appropriate workflow

---

## Spec Evolution Handling

When the spec freshness check (Phase 5, step 2) detects changes, present the user with these options:

### Option 1: Re-scan affected sections

Re-read only the changed/new section files. For each:
1. Extract requirements and compare against the existing Requirements Matrix
2. **New requirements**: Add rows with status `pending`
3. **Removed requirements**: Mark rows as `n/a` with a note ("removed in spec update YYYY-MM-DD")
4. **Changed requirements**: Flag the row as `needs_review` and note the change
5. Update the Structural Index with current file sizes
6. Update `**Spec Baseline**` date
7. Create new tasks for any added requirements

This is the best option when spec changes are localized (a few sections updated or split).

### Option 2: Proceed as-is

Acknowledge the changes without re-scanning. Log the detected changes in the Implementation Log:

```markdown
### YYYY-MM-DD - Spec changes detected (acknowledged, not re-scanned)
- New files: <list>
- Removed files: <list>
- Size changes: <list with old→new bytes>
- User chose to proceed without re-scanning
```

Continue with the current tracker state. This is appropriate when the user knows the changes don't affect in-progress work.

### Option 3: Full re-plan

Archive the current tracker with a date suffix (e.g., `.impl-tracker-myspec-archived-2025-01-15.md`), then re-run Phase 1 from scratch. Carry forward:
- Completed work from the archived tracker (mark as `complete` in the new tracker)
- Known gaps and deviations
- Implementation Log entries (summarized)

This is appropriate when spec changes are extensive or structural (major sections reorganized, new sections added).

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
- If it starts with `config`: Handle preferences (see below)
- If empty: Follow the **empty arguments procedure** below

### Config Arguments

When arguments start with `config`:
- `config` alone: Read and display current effective preferences (project file, global file, and built-in defaults)
- `config <setting> <value>`: Update `<setting>` to `<value>` in the **project-level** preferences file (`.impl-preferences.md`)
- `config --global <setting> <value>`: Update `<setting>` to `<value>` in the **global** preferences file (`~/.claude/.impl-preferences.md`)

Valid settings and values:
- `tdd`: `on`, `off`, or `ask`

Before updating, validate that the value is one of the valid options for the given setting. If invalid, inform the user and list the valid values.

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
