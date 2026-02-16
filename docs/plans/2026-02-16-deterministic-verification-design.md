# Deterministic Verification Workflow for /implement

**Date**: 2026-02-16
**Status**: Approved

## Problem

The `/implement` skill's verification phase (Phase 3) currently relies on LLM-based report assembly. Sub-agents produce markdown findings, a haiku agent concatenates them into a raw file, and the main conversation computes statistics, assigns V-item IDs, and writes the final report. This introduces:

- **Non-determinism**: Statistics, gap classification, and V-item ID assignment vary between runs on identical findings.
- **Context bloat**: The main conversation accumulates sub-agent output to compute aggregates, risking compaction during large verifications.
- **Fragility**: Markdown parsing for re-verification (matching previous V-items by section reference) is ad-hoc and error-prone.

The `/spec` skill (in `softwaredev-design`) has solved this with a structured JSON fragment schema and deterministic Python assembly. The same approach should be adopted here.

## Solution

Replace LLM-based report assembly with deterministic Python tooling:

1. Sub-agents write **JSON fragments** (one per requirement) instead of markdown findings.
2. A Python CLI tool (`verify_report.py`) assembles fragments into a report with deterministic statistics, gap classification, V-item ID assignment, and markdown rendering.
3. A blocking wait script (`wait_for_done.py`) replaces the buggy bash polling loop for agent completion detection.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Tool location | Copy into this repo (`tools/`) | Self-contained; no cross-repo dependency |
| Fragment format | JSON (matching `verification_schema.py`) | Enables deterministic validation, statistics, gap classification |
| Fix behaviour | Keep fix step (Step 6) | `/implement` is an active implementation tool, not just diagnostic |
| Output paths | `.impl-verification/<spec-name>/` | Hidden directory matching `.impl-tracker-*` convention |
| Python environment | System `python3` (no venv) | All tools are stdlib-only |

## Repository Structure Changes

### New files

```
tools/
├── verification_schema.py    # Copied from softwaredev-design — dataclasses, enums, validation,
│                              # statistics, gap classification, V-item assignment, markdown rendering
├── verify_report.py           # CLI wrapper — assembles fragments into JSON + markdown report
├── wait_for_done.py           # Blocking wait for .done marker files
└── tests/
    ├── test_verification_schema.py
    └── test_verify_report.py
```

### Modified files

- `skills/implement/SKILL.md` — Phase 3 rewritten (Steps 3-5)
- `skills/implement/references/tracker-format.md` — Verification checkpoint paths
- `skills/implement/references/workflow-quick-ref.md` — Verification checklist

## Verification Output Structure (in user projects)

```
project/
├── .impl-tracker-<spec-name>.md
└── .impl-verification/
    └── <spec-name>/
        ├── fragments/           # JSON fragments from sub-agents
        │   ├── 02-01-01.json
        │   ├── 02-01-01.done
        │   ├── 02-01-02.json
        │   └── ...
        ├── verify-<date>.json   # Assembled report (machine-readable)
        └── verify-<date>.md     # Rendered report (human-readable)
```

## Fragment Schema

Each sub-agent writes one JSON file per requirement:

```json
{
  "schema_version": "1.0.0",
  "fragment_id": "02-01-01",
  "section_ref": "§2.1.1",
  "title": "Quick Capture: Scan Barcode",
  "requirement_text": "The system MUST allow adding assets by scanning a barcode",
  "moscow": "MUST",
  "status": "partial",
  "implementation": {
    "files": [{"path": "views/capture.py", "lines": "30-45", "description": "Barcode scan view"}],
    "notes": "Handles QR and Code128 but not EAN-13"
  },
  "test_coverage": "partial",
  "tests": [{"path": "tests/test_capture.py", "lines": "10-25", "description": "Tests QR scanning"}],
  "missing_tests": ["EAN-13 format scanning"],
  "missing_implementation": ["EAN-13 barcode format support"],
  "notes": "Mobile optimisation is template-level"
}
```

Re-verification fragments add: `v_item_id`, `previous_status`, `resolution`.

## Assembly Flow

```
Sub-agents write JSON fragments + .done markers
        │
        ▼
wait_for_done.py --dir fragments/ --count N
        │
        ▼
verify_report.py --fragments-dir ... --output ...
        │
        ├── verify-<date>.json  (machine-readable)
        └── verify-<date>.md    (human-readable, deterministic rendering)
```

The Python tool handles:
- Fragment validation (hard errors on missing fields / invalid enums, soft warnings on contradictions)
- V-item ID assignment (sequential by fragment_id sort order for initial; section_ref matching for re-verification)
- Statistics: `implementation_rate = (implemented + partial × 0.5) / (total - na)`, same for test_rate
- Priority gap classification: high (MUST + not_implemented or MUST + partial + no tests), medium, low
- Markdown rendering with all report sections

## SKILL.md Phase 3 Changes

### What stays the same
- Step 0: Run tests and validate code
- Finding the Right Tracker
- Step 1: Build the Verification Plan
- Step 2: Extract Individual Requirements
- Step 6: Fix Verification Failures (reads assembled report, spawns opus fix agents)
- Re-Verification Mode user choice (from left off vs from scratch)
- One requirement = one sub-agent (hard rule)

### What changes

**Step 3 (Sub-Agent Dispatch):**
- Pre-flight: `mkdir -p .impl-verification/<name>/fragments/ && rm -f .impl-verification/<name>/fragments/*.done`
- Sub-agents run with `run_in_background: true`
- Output: JSON fragment + `.done` marker (not markdown)
- Do NOT read TaskOutput

**Steps 4+5 (Context Checkpoint + Assemble) → single deterministic step:**
- Wait: `python3 "$TOOLS_DIR/wait_for_done.py" --dir .impl-verification/<name>/fragments/ --count <N>`
- Assemble: `python3 "$TOOLS_DIR/verify_report.py" --fragments-dir ... --output ... [--previous ...]`
- Main conversation reads `.md` output to present summary

**Eliminated:**
- Haiku assembly agent
- Raw findings file (`verify-*-raw.md`)
- LLM-computed statistics and scoring
- Context health assessment for report assembly (no longer needed — assembly is one bash command)

### What doesn't change (other phases)
- Phase 1 (Planning) — untouched
- Phase 2 (Implementation, both standard and TDD) — untouched
- Phase 4 (Status) — untouched
- Phase 5 (Continue) — untouched
- Implicit activation — untouched
- Sub-agent routing / DIGEST system — untouched
- TDD preferences — untouched
- Definition of Done — untouched

## Tools Path Resolution

```bash
REPO_DIR="$(dirname "$(readlink -f ~/.claude/skills/implement/SKILL.md)")/../.."
TOOLS_DIR="$REPO_DIR/tools"
PYTHON=python3

"$PYTHON" "$TOOLS_DIR/wait_for_done.py" --dir .impl-verification/<name>/fragments/ --count <N>

"$PYTHON" "$TOOLS_DIR/verify_report.py" \
  --fragments-dir .impl-verification/<name>/fragments/ \
  --spec-path <spec-path> \
  --impl-path . \
  --project-name "<name>" \
  --output .impl-verification/<name>/verify-<date>.json
```

No venv needed — all tools are stdlib-only.
