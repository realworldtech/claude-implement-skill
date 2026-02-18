# Worktree Support Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the `/implement` skill aware of git worktrees so that when a spec/brief document indicates work should happen in a worktree, all operations target that directory.

**Architecture:** Add a worktree detection step to Phase 1 that reads the brief and determines if it specifies a worktree. Record the result in the tracker. All phases then use the tracker's worktree field to determine the implementation directory.

**Tech Stack:** Markdown skill file (SKILL.md) — no code, just prose changes.

---

### Task 1: Add Worktree Detection to Phase 1 Step 1

**Files:**
- Modify: `skills/implement/SKILL.md` — Phase 1, Step 1 section (around line 180)

**Step 1: Add worktree detection sub-step**

Insert a new sub-step at the beginning of Phase 1 Step 1 (before the STRUCT awareness check), with this content:

```markdown
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
```

**Step 2: Verify the edit**

Read the modified section to confirm it flows naturally before the existing STRUCT awareness check.

**Step 3: Commit**

```bash
git add skills/implement/SKILL.md
git commit -m "Add worktree detection to Phase 1 Step 1"
```

---

### Task 2: Add Worktree Fields to Tracker Template

**Files:**
- Modify: `skills/implement/SKILL.md` — Phase 1, Step 2 tracker template (around line 229)

**Step 1: Add worktree fields to tracker template**

In the tracker template markdown block, add two new fields after the `**Spec Baseline**:` line:

```markdown
**Worktree**: <absolute path to worktree, or "none" if working in current directory>
**Branch**: <branch name, or "none" if not specified>
```

**Step 2: Update the "Create tracker" prose**

Update the sentence "Create a tracker file **named after the spec** in the current working directory" to:

"Create a tracker file **named after the spec** in the **implementation directory** (the worktree if one was detected in Step 1, otherwise the current working directory)."

**Step 3: Commit**

```bash
git add skills/implement/SKILL.md
git commit -m "Add Worktree and Branch fields to tracker template"
```

---

### Task 3: Update Pre-Implementation Check (Phase 2)

**Files:**
- Modify: `skills/implement/SKILL.md` — Phase 2 Pre-Implementation Check (around line 335)

**Step 1: Update the pre-implementation check**

The existing check says:

> 1. A tracker file (`.impl-tracker-*.md`) exists in the current directory

Change "current directory" to "implementation directory (worktree or current directory)".

**Step 2: Also update the TDD Mode pre-implementation check**

The same language appears in Phase 2 TDD Mode (around line 551). Make the same change there.

**Step 3: Commit**

```bash
git add skills/implement/SKILL.md
git commit -m "Update pre-implementation checks for worktree awareness"
```

---

### Task 4: Update Tracker Discovery for All Phases

**Files:**
- Modify: `skills/implement/SKILL.md` — "Finding the Right Tracker" sections in Phase 3, 4, 5, and the Tracker Discovery section at the bottom

**Step 1: Update tracker discovery logic**

Every "Finding the Right Tracker" section (Phase 3 around line 734, Phase 4 around line 1152, Phase 5 around line 1175) and the Tracker Discovery section at the bottom (around line 1364) currently says to look in the "current directory". Update each to:

"Look for `.impl-tracker-*.md` in the current directory. Also check any worktree paths found in trackers already discovered — this handles the case where `/implement` is invoked from the main repo root but the tracker lives in a worktree."

**Step 2: Update the empty arguments procedure**

The empty arguments procedure (around line 1353) also searches the current directory for trackers. Add the same worktree-aware search there.

**Step 3: Commit**

```bash
git add skills/implement/SKILL.md
git commit -m "Make tracker discovery worktree-aware across all phases"
```

---

### Task 5: Update Phase 5 (Continue) for Worktree Validation

**Files:**
- Modify: `skills/implement/SKILL.md` — Phase 5 Resume Work (around line 1185)

**Step 1: Add worktree re-validation to resume flow**

In the "Resume Work" numbered list, add a new step after step 1 ("Read the tracker file to understand current state"):

```markdown
2. **Worktree validation** — if the tracker's `**Worktree**` field is not `none`:
   - Verify the worktree path still exists on disk
   - Verify it still appears in `git worktree list`
   - If `**Branch**` is not `none`, verify the worktree is on the expected branch
   - If validation fails, warn the user: the worktree may have been removed or the branch changed. Ask whether to re-create the worktree, work in the current directory instead, or abort.
   - If validation passes, set the implementation directory to the worktree path
```

Renumber subsequent steps accordingly.

**Step 2: Commit**

```bash
git add skills/implement/SKILL.md
git commit -m "Add worktree re-validation to Phase 5 (Continue)"
```

---

### Task 6: Update Recovery After Compaction

**Files:**
- Modify: `skills/implement/SKILL.md` — Recovery After Compaction section (around line 1246)

**Step 1: Add worktree to recovery steps**

In the "Recovery Steps" list, after step 2 ("Read the tracker"), add:

```markdown
3. **Check for worktree**: If the tracker's `**Worktree**` field is not `none`, validate the worktree still exists and set it as the implementation directory. All subsequent file operations should target the worktree path.
```

Renumber subsequent steps.

**Step 2: Commit**

```bash
git add skills/implement/SKILL.md
git commit -m "Add worktree recovery to compaction recovery steps"
```

---

### Task 7: Update Reference Docs

**Files:**
- Modify: `skills/implement/references/tracker-format.md` — if it exists and has a tracker template

**Step 1: Check if reference docs need updating**

Read `skills/implement/references/tracker-format.md` and `skills/implement/references/workflow-quick-ref.md`. If either contains a tracker template or references "current directory" for file operations, update them to include the worktree fields and worktree-aware language.

**Step 2: Commit**

```bash
git add skills/implement/references/
git commit -m "Update reference docs for worktree support"
```

---

### Task 8: Final Review

**Step 1: Read through the full SKILL.md**

Do a final pass to catch any remaining references to "current directory" that should say "implementation directory" or "worktree or current directory".

**Step 2: Grep for missed references**

```bash
grep -n "current directory" skills/implement/SKILL.md
grep -n "current working directory" skills/implement/SKILL.md
```

Fix any that should be worktree-aware.

**Step 3: Commit any final fixes**

```bash
git add skills/implement/SKILL.md
git commit -m "Final pass: ensure consistent worktree-aware language"
```
