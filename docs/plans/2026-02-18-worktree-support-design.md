# Design: Worktree Support for /implement

**Date:** 2026-02-18
**Status:** Approved

## Problem

The `/implement` skill assumes all work happens in the current working directory. When an external pipeline (e.g., the spec-pipeline) creates a git worktree for isolated feature work and hands off an implementation brief, `/implement` has no way to know it should work in the worktree instead of the main repo.

## Solution

Make `/implement` worktree-aware by reading the brief document for any indication that work should happen in a specific location. This is intentionally generic — the skill doesn't look for a specific section name or field format, it just reads what the document says and extracts the intent.

## Design

### 1. Worktree Detection (Phase 1, new sub-step)

After reading the spec/brief document in Phase 1 Step 1, determine whether the document specifies that implementation work should happen in a specific location. Look for any indication of:

- A worktree path where work should happen
- A branch the implementation should be on
- A project root distinct from the working location

This is generic — don't match specific section names or field formats. Read the document content and extract the intent. The brief might come from the spec-pipeline, a hand-written document, or any other source.

**Validation** (if a worktree path was identified):

1. Verify the path exists on disk
2. Confirm it's a git worktree via `git worktree list`
3. If a branch was specified, confirm the worktree is on that branch via `git -C <path> branch --show-current`
4. If validation fails, warn the user and ask whether to proceed in cwd or abort

**Effect**: Set the "implementation directory" to the worktree path. All subsequent operations use this directory instead of cwd.

### 2. Tracker Records Worktree Metadata

Two new fields in the tracker header, after the existing `**Spec Baseline**:` field:

```markdown
**Worktree**: <absolute path or "none">
**Branch**: <branch name or "none">
```

When no worktree is detected, both are set to `none` so the fields always exist and `continue`/`verify`/`status` don't need to guess.

The tracker file is created **inside the worktree directory**, since that's where all implementation work happens.

### 3. Propagation to All Phases

Every phase respects the implementation directory:

- **Phase 2 (Implementation)**: Sub-agents receive the worktree path as their working context. File paths in prompts are relative to the worktree. Test commands run inside the worktree.
- **Phase 3 (Verification)**: `.impl-verification/` is created inside the worktree. Sub-agents search for code in the worktree. Verification tools run with worktree-relative paths.
- **Phase 4 (Status)** and **Phase 5 (Continue)**: Read the tracker's `**Worktree**` field. If not `none`, validate the worktree still exists and is on the expected branch, then set the implementation directory. This is the recovery path — after context compaction, the tracker tells the skill where to work.
- **Tracker discovery**: When looking for `.impl-tracker-*.md` files (for `status`, `verify`, `continue`, `list`), search both cwd and any worktree paths from previously-found trackers. This handles invocation from the main repo root.

### 4. Sub-Agent Working Directory

Sub-agents need explicit worktree paths since they don't inherit context:

- Every sub-agent prompt that references directories or files gets the worktree absolute path
- Test run commands use the worktree path (e.g., `cd /path/to/worktree && pytest`)
- Spec file paths remain absolute (the spec may live outside the worktree, e.g., in a separate repo)

No structural change to sub-agent delegation — just ensuring paths are correct.

## Example Flow

Given a brief containing:

```markdown
## Worktree Context
- **Worktree:** /Users/dev/myproject/.worktrees/issue-4/
- **Branch:** issue/4/impl
```

1. `/implement path/to/brief.md` reads the brief
2. Detects worktree intent: `/Users/dev/myproject/.worktrees/issue-4/`
3. Validates: path exists, is in `git worktree list`, branch is `issue/4/impl`
4. Creates tracker at `/Users/dev/myproject/.worktrees/issue-4/.impl-tracker-brief.md`
5. All implementation, tests, and verification happen in that worktree
6. Sub-agents receive absolute paths into the worktree

## What Doesn't Change

- The skill's command interface (`/implement <spec>`, `status`, `verify`, `continue`, `list`, `config`)
- The tracker format (two new fields added, everything else unchanged)
- The sub-agent delegation pattern (just paths change)
- The preference system
- TDD mode workflow
- Verification tools and report format
