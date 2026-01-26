# Implementation Workflow for Claude.ai (Web)

This is the Claude.ai web version of the Implementation Skill. Since Claude.ai doesn't have the same skill/plugin system as Claude Code, this works via **Project Instructions**.

## How to Use

### Option 1: As Project Instructions

1. Create a new Project in Claude.ai
2. Go to Project Settings → Custom Instructions
3. Copy the contents of `PROJECT-INSTRUCTIONS.md` into the custom instructions
4. Upload your specification document to the Project
5. Start a conversation asking Claude to implement from the spec

### Option 2: Paste at Start of Conversation

1. Start a new conversation
2. Paste the contents of `PROJECT-INSTRUCTIONS.md`
3. Then say: "Using the workflow above, help me implement from this specification: [paste spec or describe it]"

## Workflow Commands

Since this isn't a slash-command skill, use natural language:

| Instead of... | Say... |
|---------------|--------|
| `/implement spec.md` | "Let's start implementing from [spec]. First, parse it and create a tracker." |
| `/implement status` | "Show me the current implementation status from the tracker." |
| `/implement verify` | "Let's verify the implementation against the spec section by section." |
| `/implement continue` | "Let's continue implementation. Read the tracker and pick up where we left off." |

## Tips for Claude.ai

1. **Keep the tracker in the conversation** - After Claude creates the tracker, copy it and paste it back if you start a new conversation

2. **Upload the spec to the Project** - This keeps it available across conversations

3. **Be explicit about re-reading** - Say "Before implementing Section 3.2, re-read that section from the spec"

4. **Request verification periodically** - Don't wait until the end; verify in chunks

## Limitations vs Claude Code

| Feature | Claude Code | Claude.ai Web |
|---------|-------------|---------------|
| Automatic tracker file creation | Yes | Manual (copy/paste) |
| Persistent tracker across sessions | Yes (file) | No (must re-paste) |
| Slash commands | Yes | Natural language |
| Task system integration | Yes | No |
| File editing | Yes | Outputs code to copy |

The core workflow and verification approach work the same - the main difference is manual handling of the tracker document.
