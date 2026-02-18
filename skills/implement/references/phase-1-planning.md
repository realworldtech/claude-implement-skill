# Phase 1: Planning (`/implement <spec-path>`)

When the user provides a spec path, follow these steps:

## Step 0: Offer to Clear Context

Before doing any work, ask the user if they'd like to clear the conversation context first. Implementation benefits from a clean context window — especially when invoked after a pipeline of other work (triage, spec-patching, etc.).

> Starting implementation planning. Would you like to clear context first? This gives the implementation maximum context window.
>
> If yes, run `/clear` then re-invoke `/implement <spec-path>`.

If the user declines or wants to continue, proceed to Step 1. Do not ask again if the skill is re-invoked after a `/clear`.

## Step 1: Read and Parse the Specification

**Worktree detection**: After reading the spec/brief document, determine whether it indicates that implementation work should happen in a specific directory — typically a git worktree. Look for any mention of:
- A worktree path or working directory for implementation
- A branch the implementation should be on
- A project root distinct from the implementation location

This is intentionally generic — do not look for specific section names or field formats. Read the document and extract the intent. The brief may come from any source (the spec-pipeline, a hand-written document, etc.).

**Validation** (if a worktree path was identified):
1. Verify the path exists on disk
2. Confirm it appears in `git worktree list` output (run from the project root or the worktree itself)
3. If a branch was specified, confirm the worktree is on that branch via `git -C <worktree-path> branch --show-current`
4. If validation fails, warn the user and ask whether to proceed working in the current directory or abort

**Effect**: If a valid worktree is detected, it becomes the **implementation directory** — all subsequent operations (tracker creation, file edits, test runs, verification) happen there instead of the current working directory. If no worktree is detected, the current working directory is used as before.

**STRUCT awareness check**: Before parsing the spec, look for `.spec-tracker-*.md` files in the spec's directory. If found, check for a `## Pending Structural Changes` section. If pending structural issues exist, warn the user:

> The spec has pending structural changes flagged by the `/spec` skill. These may affect implementation planning. Would you like to proceed anyway, or wait for the spec author to resolve them?

If the user chooses to proceed, note the pending issues in the tracker's Implementation Log.

**Detect spec type**: Check whether the spec has breakout section files. Look for `<!-- EXPANDED:` markers in the master document or a `sections/` directory alongside it. This determines the parsing approach:

### Single-File Specs (no breakout sections)

1. Read the entire specification document
2. Identify the document's section structure (look for patterns like `## Section N`, `### N.M`, `§N.M`, numbered headings)
3. Extract each discrete requirement with its section reference

### Multi-File Specs (breakout sections, e.g., from `/spec`)

Do NOT read all section files into main context — this will blow out the context window for large specs. Instead, build a structural index:

1. Read the master spec's **document map / table of contents only**
2. Run `wc -c` on all section files to build the structural index:
   ```
   Bash("wc -c path/to/sections/*.md")
   ```
   Record each file's byte count and compute `estimated_tokens ≈ bytes / 4`
   - **Sub-file splitting**: Section files may use letter suffixes when a section was too large and got split (e.g., `02a-core-model.md`, `02b-core-relations.md`). The glob `sections/*.md` captures these automatically. Group sub-files under their parent section number.
   - **Routing**: Sub-split sections route independently by their own size. A task referencing a parent section should include all sub-file paths in the sub-agent prompt.
3. Read only the **section headings and requirement identifiers** (MUST/SHOULD/COULD statements) from each section file — don't read full section prose into main context
4. Sub-agents will read full section files themselves during Phase 2
5. **Store the structural index in the tracker** as the spec baseline

Record the spec type in the tracker (`**Spec Type**: single-file` or `**Spec Type**: multi-file`) so that `/implement continue` knows which approach to use.

## Step 2: Create the Implementation Tracker

Create a tracker file **named after the spec** in the **implementation directory** (the worktree if one was detected in Step 1, otherwise the current working directory).

**Naming convention**: `.impl-tracker-<spec-basename>.md`

Examples:
- Spec: `docs/kaylee-billing-spec.md` → Tracker: `.impl-tracker-kaylee-billing-spec.md`
- Spec: `notification-system.md` → Tracker: `.impl-tracker-notification-system.md`
- Spec: `../specs/auth-flow.md` → Tracker: `.impl-tracker-auth-flow.md`

**See `references/tracker-format.md` for the full tracker template and field explanations.**

## Step 3: Create Tasks with Section References

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

## Step 4: Determine TDD Mode

Before presenting the plan, determine which implementation workflow to use:

1. **Read the TDD preference** using the lookup chain:
   - Check for `.impl-preferences.md` in the project directory
   - If not found (or no `tdd-mode` set), check `~/.claude/.impl-preferences.md`
   - If neither exists, use the built-in default: `on`

2. **If the preference is `on` or `off`**, record it — no user prompt needed.

3. **If the preference is `ask`**, you will present the choice as part of the plan presentation in Step 5.

## Step 5: Present the Plan

Show the user:
1. A summary of the specification structure
2. The requirements matrix from the tracker
3. The proposed task breakdown
4. The proposed implementation workflow:
   - If TDD preference was `on` or `off`: state which workflow will be used
   - If TDD preference is `ask`: present the choice:

   > **Implementation workflow**: Which workflow would you like to use?
   >
   > - **TDD mode**: Tests are written first from the spec (before any implementation code), then implementation is done to make them pass.
   > - **Standard mode**: Implementation is done first, then tests are written afterward to verify the implementation.

5. Any questions about ambiguous requirements or implementation approach

After the user approves the plan (and chooses a workflow if `ask` mode):
- **Record the choice in the tracker** by setting the `**TDD Mode**:` field to `on` or `off`.
