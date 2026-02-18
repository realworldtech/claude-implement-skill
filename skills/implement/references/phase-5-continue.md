# Phase 5: Continue (`/implement continue [spec-name]`)

## Finding the Right Tracker

1. If spec-name provided: Look for `.impl-tracker-<spec-name>.md`
2. If not provided: List all `.impl-tracker-*.md` files in the current directory and any known worktree paths
   - If exactly one: use it
   - If multiple: show list and ask which one
   - If none: inform user no active implementations found

## Resume Work

1. Read the tracker file to understand current state
2. **Worktree validation** — if the tracker's `**Worktree**` field is not `none`:
   - Verify the worktree path still exists on disk
   - Verify it still appears in `git worktree list`
   - If `**Branch**` is not `none`, verify the worktree is on the expected branch
   - If validation fails, warn the user: the worktree may have been removed or the branch changed. Ask whether to re-create the worktree, work in the current directory instead, or abort.
   - If validation passes, set the implementation directory to the worktree path
3. **Spec freshness check** — detect whether the spec has changed since the last session:
   - **Multi-file specs**: Re-run `wc -c path/to/sections/*.md` and compare against the stored Structural Index in the tracker:
     - **New files**: Files present on disk but not in the index
     - **Removed files**: Files in the index but no longer on disk
     - **Size changes**: Any file whose byte count changed by >20% from the stored value
     - **Sub-split patterns**: A previously single file now has letter-suffix variants
   - **Single-file specs**: Compare the file size against the tracker's `**Spec Baseline**` date — if the file's modification time is newer, flag it
   - **STRUCT check**: Look for `.spec-tracker-*.md` files and check for `## Pending Structural Changes`
   - **When changes detected**: Present the user with 3 options (see Spec Evolution Handling below)
   - **When no changes detected**: Proceed silently
4. **Check the `**TDD Mode**:` field** — use the TDD workflow (`references/phase-2-tdd.md`) or standard workflow (`references/phase-2-implementation.md`) accordingly
5. Read the task list
6. Identify the next pending task
7. **Re-read the relevant spec sections** before continuing
8. Resume implementation using the appropriate workflow

---

## Spec Evolution Handling

When the spec freshness check detects changes, present the user with these options:

### Option 1: Re-scan affected sections

Re-read only the changed/new section files. For each:
1. Extract requirements and compare against the existing Requirements Matrix
2. **New requirements**: Add rows with status `pending`
3. **Removed requirements**: Mark rows as `n/a` with a note ("removed in spec update YYYY-MM-DD")
4. **Changed requirements**: Flag the row as `needs_review` and note the change
5. Update the Structural Index with current file sizes
6. Update `**Spec Baseline**` date
7. Create new tasks for any added requirements

Best when spec changes are localized.

### Option 2: Proceed as-is

Acknowledge the changes without re-scanning. Log in the Implementation Log:

```markdown
### YYYY-MM-DD - Spec changes detected (acknowledged, not re-scanned)
- New files: <list>
- Removed files: <list>
- Size changes: <list with old→new bytes>
- User chose to proceed without re-scanning
```

Appropriate when the user knows the changes don't affect in-progress work.

### Option 3: Full re-plan

Archive the current tracker with a date suffix, then re-run Phase 1 from scratch. Carry forward:
- Completed work from the archived tracker
- Known gaps and deviations
- Implementation Log entries (summarized)

Appropriate when spec changes are extensive or structural.
