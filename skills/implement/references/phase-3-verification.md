# Phase 3: Verification (`/implement verify [spec-name]`)

**Important**: Verification requires careful reasoning to catch subtle gaps. Use `model: "opus"` when delegating verification work to sub-agents.

## Step 0: Run Tests and Validate Code

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

## Finding the Right Tracker

1. If spec-name provided: Look for `.impl-tracker-<spec-name>.md`
2. If not provided: List all `.impl-tracker-*.md` files in the current directory and any known worktree paths
   - If exactly one: use it
   - If multiple: show list and ask which one
   - If none: inform user no active implementations found

## Resolve the Implementation Directory

After finding the tracker, check its `**Worktree**` field:
- If not `none`: validate the worktree path exists and use it as the **implementation directory** for all subsequent steps (tests, verification artifacts, sub-agent search paths)
- If `none`: use the current working directory

All paths below that reference `.impl-verification/`, `--impl-path`, or `Search directory:` should resolve relative to the **implementation directory**, not necessarily the current working directory.

## Step 1: Build the Verification Plan (Main Conversation)

Read ONLY these files in the main conversation:
1. The implementation tracker (`.impl-tracker-<name>.md`) — to understand spec structure and file references
2. The spec document's **structure/table of contents only** — to know which sections exist
3. **Check for previous verification reports**: `Glob("<impl-dir>/.impl-verification/<spec-name>/verify-*.json")` — if one or more exist, read the **most recent** report. This triggers **re-verification mode** (see below)

**Do NOT read full spec sections or implementation files in the main conversation.**

## Step 2: Extract Individual Requirements (Main Conversation)

Read each spec section and extract its **individual requirements** — the specific MUST/SHOULD/COULD statements or concrete behavioural expectations, not the section headings.

**Key distinction**: A spec subsection like "§2.1 Quick Capture" is a *topic area*, not a single requirement. It typically contains multiple individual requirements. Each of those is a requirement — that's the level of granularity you need.

For each section:
1. Read the section content
2. Extract each individual requirement with its §N.M reference and a one-line summary
3. Note any implementation hints from the tracker (file:line references)
4. Release the section content from context — you only need the requirement list going forward

Build a flat list:
```
§2.1.1 — Quick capture: scan barcode to add asset — impl hint: views/capture.py:30
§2.1.2 — Quick capture: pre-fill fields from barcode data — impl hint: views/capture.py:55
§2.1.3 — Quick capture: manual entry fallback — no hint
...
```

A typical spec section with 15 subsections should produce **30-60+ individual requirements**, NOT 15.

## Tools Setup

Before running verification sub-agents, resolve the tools directory:

```bash
REPO_DIR="$(dirname "$(readlink -f ~/.claude/skills/implement/SKILL.md)")/../.."
TOOLS_DIR="$REPO_DIR/tools"
PYTHON=python3
```

## Step 3: Requirement-Level Verification via Sub-Agents (Parallel)

**Pre-flight**: Create the fragments directory and clear any stale markers:

```bash
mkdir -p <impl-dir>/.impl-verification/<spec-name>/fragments/ && rm -f <impl-dir>/.impl-verification/<spec-name>/fragments/*.done
```

Where `<impl-dir>` is the implementation directory resolved above (worktree path or cwd).

Dispatch verification sub-agents using the prompt template at `prompts/verify-requirement.md`. **One requirement per sub-agent** — this is a hard rule. See the prompt template for the full dispatch pattern, JSON format, and granularity examples.

## Step 4: Assemble Verification Report (Deterministic)

**Context protection**: Do NOT call `TaskOutput` on verification agents. Wait for `.done` markers, then run the Python assembly tool.

**Wait for completion:**

```bash
"$PYTHON" "$TOOLS_DIR/wait_for_done.py" --dir <impl-dir>/.impl-verification/<spec-name>/fragments/ --count <number of requirements dispatched>
```

**Assemble the report:**

```bash
"$PYTHON" "$TOOLS_DIR/verify_report.py" \
  --fragments-dir <impl-dir>/.impl-verification/<spec-name>/fragments/ \
  --spec-path <spec-path> \
  --impl-path <impl-dir> \
  --project-name "<spec-name>" \
  --output <impl-dir>/.impl-verification/<spec-name>/verify-<date>.json
```

For re-verification, add `--previous` pointing to the previous report JSON:

```bash
"$PYTHON" "$TOOLS_DIR/verify_report.py" \
  --fragments-dir <impl-dir>/.impl-verification/<spec-name>/fragments/ \
  --spec-path <spec-path> \
  --impl-path <impl-dir> \
  --project-name "<spec-name>" \
  --output <impl-dir>/.impl-verification/<spec-name>/verify-<date>.json \
  --previous <impl-dir>/.impl-verification/<spec-name>/verify-<prev-date>.json
```

This produces:
- `<impl-dir>/.impl-verification/<spec-name>/verify-<date>.json` — machine-readable report
- `<impl-dir>/.impl-verification/<spec-name>/verify-<date>.md` — human-readable report

**The report format is defined in `tools/verification_schema.py:render_markdown()`.** Do not write report markdown manually.

**Present to user:**

> **Verification complete.** See the full report at `<impl-dir>/.impl-verification/<spec-name>/verify-<date>.md`.
>
> **Results**: X of Y requirements implemented, A of B have test coverage.
> Implementation rate: Z%, Test rate: W%
>
> **Critical gaps** (if any):
> - <top 3 from priority_gaps with priority "high">

## Step 5: Fix Verification Failures

Use the prompt template at `prompts/fix-verification-gap.md` to fix gaps. **Always use Opus.**

After each fix:
1. Read the fix summary from `<impl-dir>/.impl-work/<spec-name>/fix-summary.json` — do NOT re-analyse conversational output
2. Run tests to confirm fix works
3. Re-verify that specific requirement (single sub-agent, **background**, same pattern as Step 3 — writes JSON fragment + `.done` marker)
4. Wait for `.done`, then read the updated fragment to confirm the fix resolved the V-item
5. Update the tracker
6. Repeat until all gaps are resolved

## Re-Verification Mode

When a previous verification report exists, the verify command runs in **re-verification mode**. Ask the user:

> I found a previous verification report with X open V-items.
>
> 1. **Re-verify from where we left off** — Check only the open V-items, plus spot-check for regressions
> 2. **Full re-verification from scratch** — Re-audit all requirements, but carry forward V-item IDs

| Aspect | Initial | From left off | From scratch |
|--------|---------|--------------|-------------|
| Scope | All requirements | Open V-items + spot-check | All again |
| V-item IDs | Fresh | Carried forward | Carried forward |
| Token cost | Full | ~30-50% | ~100% |

### Re-Verification from Where We Left Off

1. Read the most recent report. Extract open V-items and the ID counter.
2. Categorize: **Open** (Partial/Not Implemented, or test coverage Partial/None) vs **Passed** (Implemented + Full coverage).
3. For open items: use `prompts/reverify-requirement.md` to dispatch re-verification agents.
4. For passed items: lightweight spot-check (cluster 5-10 into one agent).
5. Check for new requirements if spec was updated.

### Re-Verification from Scratch

Run the full initial verification flow, but:
- Match findings to previous V-items by §N.M reference
- Reuse existing V-item IDs
- Include resolution status for previously flagged items

### V-Item Lifecycle

```
Initial verification → V1 created (status: Partial)
Re-verification 1   → V1 checked (resolution: PARTIALLY FIXED)
Re-verification 2   → V1 checked (resolution: FIXED) — item closed
```

- **FIXED**: Fully resolved
- **PARTIALLY FIXED**: Progress made, not fully resolved
- **NOT FIXED**: No meaningful progress
- **REGRESSED**: Previously fixed, now broken again

V-item IDs are **permanent** — once assigned, they stay forever across re-verification runs.

## Context Efficiency Rules

1. Main conversation reads ONLY the tracker and spec structure
2. Pass spec requirement text directly in sub-agent prompts
3. Sub-agents DO read implementation files
4. Cap sub-agent output — structured findings only
5. One requirement per sub-agent
6. Do NOT call TaskOutput on verification agents — wait for `.done` markers

## Definition of Done

Implementation is ONLY complete when ALL of these are true:

- [ ] **Tests pass**: All tests in the test suite pass
- [ ] **No lint/type errors**: Code passes all configured checks
- [ ] **Code runs**: Application starts/compiles without errors
- [ ] **Spec verification complete**: All requirements implemented or documented as N/A
- [ ] **Tracker updated**: Requirements matrix reflects final state with file:line references
- [ ] **Gaps documented**: Any remaining gaps are documented with severity and rationale

**Never claim "done" without running tests first.**
