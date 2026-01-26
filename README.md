# Implementation Skill for Claude Code

A Claude Code skill for implementing features from specification documents with systematic tracking and verification.

## Why This Exists

When you give Claude a detailed business process document or specification to implement, something interesting happens:

**The start goes well.** Claude reads the document, understands the requirements, breaks the work into logical steps, and begins implementing with clear references to the spec.

**Then drift happens.** As the conversation grows and context compacts (Claude's way of managing long conversations), the connection to the source document weakens. Claude starts working from memory of the spec rather than the spec itself. Requirements get missed. Implementation choices diverge from what was specified. The longer the work continues, the worse this gets.

**Verification becomes a rescue mission.** At the end, when you ask Claude to verify the implementation against the spec, it often reveals gaps - requirements that were missed, behaviours that don't match, edge cases that were forgotten. The gap analysis works great, but by then you've already built the wrong thing.

### The Core Insight

The problem isn't that Claude can't follow a spec - it's that **Claude loses its anchor to the spec** as work progresses. The solution is to create a persistent reference that survives context compaction and forces Claude to re-read the relevant spec sections before each piece of work.

**Section references (§2.4, §9.1, Section 3.2) are stable anchors.** They're short, memorable, and point directly back to the source. If every task, every tracker entry, and every verification item includes section references, Claude can always find its way back to the source of truth.

## How It Works

### The Tracker File

When you start an implementation, the skill creates a tracker file (`.impl-tracker-<spec-name>.md`) that maps every requirement to:
- Its section reference in the spec
- Its implementation status
- Where it was implemented (file:line references)

This tracker is the **bridge** between compacted context and the source document. Even when Claude forgets the details of the spec, reading the tracker tells it exactly which sections to re-read.

### The Key Behaviour

**Before every task**, Claude:
1. Reads the tracker to find which spec sections are relevant
2. Re-reads those sections from the original spec
3. Works from the source of truth, not from memory

This simple discipline - always go back to the spec - prevents most implementation drift.

### Verification

Instead of hoping the implementation matches the spec, the skill provides systematic verification:
1. Re-read the entire spec fresh
2. Walk through section by section
3. Check each requirement against actual implementation
4. Produce a gap analysis with specific section references

The gap analysis format makes it clear exactly what's missing and where to find the requirement in the spec.

## Installation

### Claude Code

Clone to your skills directory:

```bash
git clone https://github.com/realworldtech/claude-implement-skill ~/.claude/skills/implement
```

Or for project-level installation:

```bash
git clone https://github.com/realworldtech/claude-implement-skill .claude/skills/implement
```

### Claude.ai (Web)

See the `claude-web/` directory for project instructions you can paste into a Claude.ai Project.

## Usage

### Start an Implementation

```
/implement path/to/your-spec.md
```

Claude will:
1. Read and parse the specification
2. Extract requirements with section references
3. Create a tracker file
4. Present a plan for approval

### Check Status

```
/implement status
/implement status spec-name    # if multiple implementations active
```

### Resume Work

```
/implement continue
```

Claude will read the tracker, find the next pending task, re-read the relevant spec sections, and continue.

### Verify Implementation

```
/implement verify
```

Produces a section-by-section gap analysis showing what's complete, partial, or missing.

### List Active Implementations

```
/implement list
```

## Writing Specs for This Workflow

Specifications work best with this skill when they:

- **Use numbered sections** (§1.1, §2.3, Section 4.2) - these become the stable anchors
- **Have discrete, testable requirements** - not vague descriptions but specific behaviours
- **Include expected inputs/outputs** - what goes in, what comes out
- **Separate must-have from nice-to-have** - helps prioritise gaps

See `skills/implement/examples/sample-spec.md` for a well-structured example.

## Example Gap Analysis Output

```
## Gap Analysis: Ticket Processing Spec

### Section 2: Workflow Triggers

| Section | Requirement | Status | Notes |
|---------|-------------|--------|-------|
| §2.1 | In-flight triggers | Complete | InFlightStateStep handles this |
| §2.2 | Closure triggers | Complete | ClosureProcessingStep |
| §2.4 | Merge detection gate | GAP | Detects but doesn't post to target |

### Gap Details

#### §2.4 - Merge Detection Gate
**Spec says**: "Merged tickets should generate summary and post to TARGET ticket"
**Current state**: Detects merge, skips processing
**Gap**: Does not post summary to target ticket
**Suggested fix**: Add target ticket lookup and comment posting in EdgeCaseHandler

### Summary

| Status | Count |
|--------|-------|
| Complete | 18 |
| Partial | 4 |
| Gap | 2 |

### Priority Gaps
1. [HIGH] §2.4 - Merge workflow incomplete
2. [MEDIUM] §9.1 - Follow-up action extraction not implemented
```

## Project Structure

```
├── .claude-plugin/
│   └── plugin.json              # Plugin manifest
├── skills/
│   └── implement/
│       ├── SKILL.md             # Main skill definition
│       ├── references/
│       │   ├── tracker-format.md
│       │   └── workflow-quick-ref.md
│       └── examples/
│           └── sample-spec.md
├── claude-web/
│   ├── PROJECT-INSTRUCTIONS.md  # For Claude.ai web users
│   └── README.md
├── README.md
└── LICENSE
```

## License

MIT - See [LICENSE](LICENSE)

## Contributing

Issues and pull requests welcome at [github.com/realworldtech/claude-implement-skill](https://github.com/realworldtech/claude-implement-skill).
