# Implementation Skill for Claude Code

A Claude Code skill that helps implement features from specification documents while maintaining a persistent connection to source requirements throughout the work.

## The Problem This Solves

When implementing complex features from a spec document, Claude tends to:
- Start well by reading the document and breaking work into steps
- Gradually lose connection to the source document as context compacts
- Miss requirements or drift from the spec as work progresses

This skill solves this by:
- Creating a **tracker file** that maps requirements to implementation status
- Ensuring Claude **re-reads relevant spec sections** before each task
- Providing **systematic verification** that walks through the spec section-by-section

## Installation

### Via Plugin Marketplace (Recommended)

If your organisation has a plugin marketplace set up:

```bash
/plugin install implement@your-marketplace
```

### Via Git

Clone directly to your Claude Code skills directory:

```bash
git clone https://github.com/realworldtech/claude-implement-skill ~/.claude/skills/implement
```

Or for project-level installation:

```bash
git clone https://github.com/realworldtech/claude-implement-skill .claude/skills/implement
```

### Manual Installation

Copy the `skills/implement` directory to `~/.claude/skills/implement`.

## Usage

### Start an Implementation

```
/implement path/to/your-spec.md
```

Claude will:
1. Read and parse the specification
2. Extract requirements with section references (e.g., *2.4, *9.1)
3. Create a tracker file (`.impl-tracker-your-spec.md`)
4. Create tasks with section references
5. Present a plan for approval

### Check Status

```
/implement status
/implement status your-spec    # If multiple implementations active
```

### Resume Work

```
/implement continue
/implement continue your-spec
```

### Verify Implementation

```
/implement verify
```

Produces a gap analysis report showing:
- Section-by-section verification
- Complete/Partial/Gap status for each requirement
- Detailed gap descriptions with suggested fixes

### List Active Implementations

```
/implement list
```

## How It Works

### The Tracker File

The tracker (`.impl-tracker-<spec-name>.md`) is the bridge between compacted context and the source document. It contains:

- **Requirements Matrix**: Each spec section mapped to status and implementation location
- **Known Gaps**: Identified issues with severity and suggested fixes
- **Implementation Log**: Session-by-session history of what was done

Even when Claude's context compacts, reading the tracker provides enough anchors to:
1. Know what spec sections are relevant
2. Re-read those sections before continuing
3. Maintain accuracy throughout long implementations

### The Key Behaviour

**Before every task**, Claude:
1. Reads the tracker to get section references
2. Re-reads those sections from the original spec
3. Works from the source of truth, not memory

This prevents drift by ensuring Claude always references the spec, not a compacted summary.

## Writing Specs for This Workflow

Specs work best when they:
- Use **numbered sections** (*1.1, *2.3, etc.)
- Have **discrete, testable requirements**
- Include **expected inputs/outputs** where applicable
- Separate **must have** from **nice to have**

See `skills/implement/examples/sample-spec.md` for a well-structured example.

## Files

```
skills/implement/
├── SKILL.md                           # Main skill definition
├── references/
│   ├── tracker-format.md              # Detailed tracker format
│   └── workflow-quick-ref.md          # Quick reference card
└── examples/
    └── sample-spec.md                 # Example specification
```

## License

MIT
