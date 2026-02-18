# Verification Prompt — Single Requirement

Use this template when dispatching a verification sub-agent for ONE requirement. **Always use Opus** for verification. **Always run in background** — do NOT read TaskOutput.

**HARD RULE: One requirement per sub-agent.** Do NOT batch multiple requirements into one agent. Do NOT group by subsection. Do NOT cluster "related" requirements.

The only exception: if two requirements are literally about the same line of code (e.g., "field MUST be required" and "field MUST be validated as email"), you MAY put those two in one agent. Never more than 2, and only when they test the exact same code path.

## Dispatch Pattern

```python
# Pattern: ONE requirement = ONE sub-agent

# 1. Extract the single requirement text (from Step 2)
req_text = "§2.1.1: The system MUST allow adding assets by scanning a barcode."

# 2. Build implementation hints from tracker (if available)
impl_hints = "Implementation tracker references: views/capture.py:30"

# 3. Delegate — one requirement, one agent
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

## Granularity Examples

**Anti-pattern — DO NOT do this:**
```
Agent 1: §2.1 (Quick Capture), §2.2 (Asset Management), §2.3 (Checkout), §2.4 (Barcodes)
Agent 2: §2.5 (NFC), §2.6 (Search), §2.7 (Stocktake), §2.8 (Bulk Ops), §2.9 (Exports)
```

**Correct pattern:**
```
Agent 1:  §2.1.1 — Scan barcode to add asset
Agent 2:  §2.1.2 — Pre-fill fields from barcode data
Agent 3:  §2.1.3 — Manual entry fallback
Agent 4:  §2.2.1 — Asset detail view
...
Agent 35: §8.1.1 — Unit test coverage target
```

Yes, this means 20-40+ parallel agents for a medium-sized spec. That's correct and intended.
