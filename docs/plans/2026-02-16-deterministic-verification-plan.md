# Deterministic Verification Workflow Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace LLM-based verification report assembly in the /implement skill with deterministic JSON fragment schema and Python tooling.

**Architecture:** Copy `verification_schema.py`, `verify_report.py`, and `wait_for_done.py` from softwaredev-design into `tools/`. Update SKILL.md Phase 3 so sub-agents write JSON fragments to `.impl-verification/<spec-name>/fragments/`, then `verify_report.py` assembles reports deterministically. Update reference docs for new paths and workflow.

**Tech Stack:** Python 3 (stdlib only), JSON schema, pytest

---

### Task 1: Create tools directory and copy Python tools

**Files:**
- Create: `tools/verification_schema.py`
- Create: `tools/verify_report.py`
- Create: `tools/wait_for_done.py`

**Step 1: Create tools directory**

Run: `mkdir -p tools/tests`

**Step 2: Copy verification_schema.py**

Copy from `~/dev/softwaredev-design/tools/verification_schema.py` to `tools/verification_schema.py`. This is a direct copy — no modifications needed. The file is stdlib-only (json, logging, dataclasses, enum, pathlib).

Run: `cp ~/dev/softwaredev-design/tools/verification_schema.py tools/verification_schema.py`

**Step 3: Copy verify_report.py**

Copy from `~/dev/softwaredev-design/tools/verify_report.py` to `tools/verify_report.py`. Direct copy, no modifications.

Run: `cp ~/dev/softwaredev-design/tools/verify_report.py tools/verify_report.py`

**Step 4: Copy wait_for_done.py**

Copy from `~/dev/softwaredev-design/tools/wait_for_done.py` to `tools/wait_for_done.py`. Direct copy, no modifications.

Run: `cp ~/dev/softwaredev-design/tools/wait_for_done.py tools/wait_for_done.py`

**Step 5: Commit**

```bash
git add tools/verification_schema.py tools/verify_report.py tools/wait_for_done.py
git commit -m "Copy verification tools from softwaredev-design

Brings verification_schema.py (JSON fragment schema, validation,
statistics, gap classification, V-item assignment, markdown rendering),
verify_report.py (CLI wrapper), and wait_for_done.py (blocking .done
marker polling) into this repo. All stdlib-only, no modifications."
```

---

### Task 2: Copy and run test suite

**Files:**
- Create: `tools/tests/__init__.py`
- Create: `tools/tests/test_verification_schema.py`
- Create: `tools/tests/test_verify_report.py`

**Step 1: Copy test files**

```bash
cp ~/dev/softwaredev-design/tools/tests/test_verification_schema.py tools/tests/test_verification_schema.py
cp ~/dev/softwaredev-design/tools/tests/test_verify_report.py tools/tests/test_verify_report.py
touch tools/tests/__init__.py
```

**Step 2: Update test_verify_report.py TOOL_PATH**

The `TOOL_PATH` in `test_verify_report.py` references `Path(__file__).parent.parent / "verify_report.py"` — this should already resolve correctly since the directory structure mirrors the original. Verify this is the case.

**Step 3: Run tests to verify everything works**

Run: `cd /Users/andrewya/dev/implementation-skill && python3 -m pytest tools/tests/ -v`

Expected: All 65+ tests pass. If any fail, debug and fix before proceeding.

**Step 4: Commit**

```bash
git add tools/tests/
git commit -m "Add test suite for verification tools

65 tests covering enums, dataclasses, fragment validation, loading,
statistics computation, priority gap classification, V-item assignment,
report assembly, JSON round-trip, markdown rendering, and CLI tool."
```

---

### Task 3: Rewrite SKILL.md Phase 3 — Steps 3-5

This is the core change. Replace the current Steps 3-5 (sub-agent dispatch with markdown output, haiku assembly, LLM report generation) with JSON fragment dispatch and deterministic Python assembly.

**Files:**
- Modify: `skills/implement/SKILL.md` (lines ~780-910, the Step 3 sub-agent prompt, Step 4 context checkpoint, and Step 5 report assembly)

**Step 1: Add TOOLS_DIR resolution block**

Insert at the start of Phase 3 (after the "### Step 2" section ends, before "### Step 3"), a tools setup block:

```markdown
### Tools Setup

Before running verification sub-agents, resolve the tools directory:

\`\`\`bash
REPO_DIR="$(dirname "$(readlink -f ~/.claude/skills/implement/SKILL.md)")/../.."
TOOLS_DIR="$REPO_DIR/tools"
PYTHON=python3
\`\`\`

These variables are used in Steps 3-5 below.
```

**Step 2: Rewrite Step 3 (Sub-Agent Dispatch)**

Replace the current Step 3 content (lines ~780-857) with:

- Add pre-flight: `mkdir -p .impl-verification/<spec-name>/fragments/ && rm -f .impl-verification/<spec-name>/fragments/*.done`
- Change sub-agents to `run_in_background: true`
- Change output format from markdown to JSON fragment
- Agent writes to `.impl-verification/<spec-name>/fragments/<fragment_id>.json` + `.done` marker
- Fragment naming: §2.1.1 → `02-01-01.json`
- Include JSON schema example in the sub-agent prompt template
- Add MoSCoW extraction instruction (agent determines MUST/SHOULD/COULD from requirement text)

The sub-agent prompt template changes from:

```
## Report Format (use ONLY this format)

### §2.1.1 — Quick Capture: Scan Barcode

**Spec says**: <exact quote or summary of the requirement>
**Status**: Implemented / Partial / Not Implemented / N/A
...
```

To:

```
## Output — Write findings to disk as JSON

Write your findings to: .impl-verification/<spec-name>/fragments/02-01-01.json

Use this EXACT JSON format:
{
  "schema_version": "1.0.0",
  "fragment_id": "02-01-01",
  "section_ref": "§2.1.1",
  "title": "Quick Capture: Scan Barcode",
  "requirement_text": "<exact quote or summary>",
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

After writing the JSON file, write a completion marker:
.impl-verification/<spec-name>/fragments/02-01-01.done (contents: just "done").
The .done marker MUST be the last file you write.
```

**Step 3: Replace Steps 4+5 with deterministic assembly**

Remove the current Step 4 (Context Checkpoint with 4a/4b/4c sub-steps) and Step 5 (Assemble Verification Report with LLM-generated markdown template). Replace with:

```markdown
### Step 4: Assemble Verification Report (Deterministic)

**Context protection**: Do NOT call `TaskOutput` on verification agents. With 20-40+ parallel agents, reading their output would fill the context window. Instead, wait for `.done` markers, then run the Python assembly tool.

**Wait for completion:**

\`\`\`bash
"$PYTHON" "$TOOLS_DIR/wait_for_done.py" --dir .impl-verification/<spec-name>/fragments/ --count <number of requirements dispatched>
\`\`\`

**Assemble the report:**

\`\`\`bash
"$PYTHON" "$TOOLS_DIR/verify_report.py" \
  --fragments-dir .impl-verification/<spec-name>/fragments/ \
  --spec-path <spec-path> \
  --impl-path . \
  --project-name "<spec-name>" \
  --output .impl-verification/<spec-name>/verify-<date>.json
\`\`\`

For re-verification, add `--previous` pointing to the previous report JSON:

\`\`\`bash
"$PYTHON" "$TOOLS_DIR/verify_report.py" \
  --fragments-dir .impl-verification/<spec-name>/fragments/ \
  --spec-path <spec-path> \
  --impl-path . \
  --project-name "<spec-name>" \
  --output .impl-verification/<spec-name>/verify-<date>.json \
  --previous .impl-verification/<spec-name>/verify-<prev-date>.json
\`\`\`

This produces:
- `.impl-verification/<spec-name>/verify-<date>.json` — machine-readable report
- `.impl-verification/<spec-name>/verify-<date>.md` — human-readable report

The tool deterministically handles:
- Fragment validation (hard errors on missing fields / invalid enums)
- V-item ID assignment (sequential by fragment_id sort order for initial; section_ref matching for re-verification)
- Statistics: implementation_rate, test_rate, must_implementation_rate, MoSCoW breakdowns
- Priority gap classification (high/medium/low)
- Markdown rendering with all report sections

**Present to user:**

Read the `.md` report file (or just its Summary and Scorecard sections) and present results:

> **Verification complete.** See the full report at `.impl-verification/<spec-name>/verify-<date>.md`.
>
> **Results**: X of Y requirements implemented, A of B have test coverage.
> Implementation rate: Z%, Test rate: W%
>
> **Critical gaps** (if any):
> - <top 3 from priority_gaps with priority "high">
```

**Step 4: Update the re-verification sub-agent prompt**

In the re-verification section (~lines 1055-1093), update the sub-agent prompt to write JSON with the extra re-verification fields:

```json
{
  "schema_version": "1.0.0",
  "fragment_id": "03-02",
  "section_ref": "§3.2",
  "title": "AI Thumbnail Generation",
  "requirement_text": "...",
  "moscow": "MUST",
  "status": "implemented",
  "v_item_id": "V12",
  "previous_status": "partial",
  "resolution": "fixed",
  "implementation": { ... },
  "test_coverage": "full",
  "tests": [ ... ],
  "missing_tests": [],
  "missing_implementation": [],
  "notes": "Switched from full URL to relative path"
}
```

Valid resolution values: `fixed`, `partially_fixed`, `not_fixed`, `regressed`.

**Step 5: Remove the markdown report template**

Delete the large markdown report template block (lines ~920-985) that showed the `# Implementation Verification: <Spec Name>` format. This is now generated by `render_markdown()` in `verification_schema.py`. Keep a brief note saying the report format is defined in `tools/verification_schema.py:render_markdown()`.

**Step 6: Update Context Efficiency Rules**

Replace rule 6 ("Write findings directly to the report file — don't accumulate results in main conversation context") with:

```
6. **Do NOT call TaskOutput on verification agents** — wait for `.done` markers, then run `verify_report.py` for deterministic assembly
```

Remove references to "haiku assembly agent" and "raw findings file".

**Step 7: Verify the edit**

Read through the modified Phase 3 section to ensure internal consistency:
- All references to markdown fragments → JSON fragments
- All references to haiku assembly → removed
- All references to raw findings file → removed
- verify-<name>-<date>.md path now inside .impl-verification/
- Re-verification mode still offers "from left off" vs "from scratch"

**Step 8: Commit**

```bash
git add skills/implement/SKILL.md
git commit -m "Rewrite Phase 3 verification to use deterministic JSON fragments

Sub-agents now write JSON fragments matching verification_schema.py
instead of markdown. Report assembly uses verify_report.py (Python)
instead of LLM. Eliminates haiku assembly agent, raw findings file,
and LLM-computed statistics. V-item IDs, statistics, gap classification,
and markdown rendering are all deterministic."
```

---

### Task 4: Update reference docs

**Files:**
- Modify: `skills/implement/references/workflow-quick-ref.md` (lines ~64-97)
- Modify: `skills/implement/references/tracker-format.md`

**Step 1: Update workflow-quick-ref.md verification checklist**

Replace the current "Verification Checklist" section (lines 64-97) with updated steps that reflect the new flow:

```markdown
## Verification Checklist

During verification:

**FIRST - Validate code works:**
- [ ] **Run full test suite** - fix any failures before proceeding
- [ ] **Run linting/type checking** - fix any errors
- [ ] **Verify code compiles/runs** - no import errors, syntax errors

**THEN - Extract individual requirements:**
- [ ] Read spec structure (NOT full content) in main context
- [ ] Extract individual MUST/SHOULD/COULD requirements (not section headings)
- [ ] Build flat list: §N.M — one-line summary — impl hint from tracker
- [ ] A section with 15 subsections should produce 30-60+ requirements, NOT 15

**THEN - Verify at requirement level (parallel sub-agents):**
- [ ] Pre-flight: `mkdir -p .impl-verification/<name>/fragments/ && rm -f .impl-verification/<name>/fragments/*.done`
- [ ] ONE requirement = ONE sub-agent (hard rule)
- [ ] Each agent writes JSON fragment + `.done` marker to `.impl-verification/<name>/fragments/`
- [ ] Use `run_in_background: true` — do NOT read TaskOutput
- [ ] Check for previous verify reports — triggers re-verification mode if found

**THEN - Assemble report (deterministic):**
- [ ] Wait: `python3 "$TOOLS_DIR/wait_for_done.py" --dir .impl-verification/<name>/fragments/ --count <N>`
- [ ] Assemble: `python3 "$TOOLS_DIR/verify_report.py" --fragments-dir ... --output ...`
- [ ] Read the `.md` output to present summary to user
- [ ] For re-verification: add `--previous` flag pointing to previous report JSON

**Never claim verification is complete if tests are failing.**
```

**Step 2: Update tracker-format.md verification checkpoint**

In the "After verification" section (lines 198-203), update the verification report path reference:

```markdown
### After verification:
1. **Run full test suite first** - verification is meaningless if tests fail
2. Update all statuses in Requirements Matrix
3. Add new gaps to Known Gaps
4. Update Implementation Log with verification results
5. Note test pass/fail status in log entry
6. Verification reports stored in `.impl-verification/<spec-name>/`
```

**Step 3: Commit**

```bash
git add skills/implement/references/workflow-quick-ref.md skills/implement/references/tracker-format.md
git commit -m "Update reference docs for deterministic verification workflow

Verification checklist now uses JSON fragments, .done markers, and
verify_report.py. Tracker format references .impl-verification/ path."
```

---

### Task 5: End-to-end validation

**Step 1: Run the full test suite one more time**

Run: `python3 -m pytest tools/tests/ -v`

Expected: All tests pass.

**Step 2: Verify SKILL.md is internally consistent**

Read through Phase 3 in full and check:
- No references to old markdown fragment format remain
- No references to haiku assembly agent remain
- No references to `verify-*-raw.md` remain
- All paths use `.impl-verification/` pattern
- Re-verification mode still works (both "from left off" and "from scratch")
- Fix step (Step 6) references the correct report path
- Context Efficiency Rules are consistent with new flow

**Step 3: Verify reference docs are consistent**

Check that workflow-quick-ref.md and tracker-format.md don't reference the old flow.

**Step 4: Final commit (if any fixes needed)**

Only if corrections were needed in Step 2-3.
