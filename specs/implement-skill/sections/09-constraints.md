# §9 Constraints, Assumptions & Out of Scope

> Part of [Master Spec](../spec.md)

---

## §9.1 Platform Constraints

The `/implement` skill is tightly coupled to its execution environment and cannot degrade gracefully if certain dependencies are unavailable.

### Hard Dependencies

- **Claude Code CLI**: Requires the full Claude Code platform. The skill uses platform-specific features that have no fallback:
  - Task tool for spawning background agents
  - TaskCreate, TaskUpdate, TaskList, TaskGet for persistence across context compaction
  - Sub-agent spawning and parallel task delegation
  - Background task execution (`run_in_background` parameter)

- **Model Tier Availability**: Hard dependency on three Claude model tiers being available during a single implementation session (see NFR-COST-01 and NFR-COST-02 for the routing rules that govern when each tier is selected):
  - **Haiku** (fast, cost-efficient): Boilerplate tasks, simple spec parsing, routine delegation
  - **Sonnet** (balanced): Standard implementation tasks, moderate complexity work
  - **Opus** (most capable): Verification (always), gap fixing (always), complex implementation, planning for large specs

  **No automatic fallback**: Tier selection is quality-critical — especially for verification, where Opus is required. The skill does NOT automatically fall back to a lower tier if the selected tier is unavailable. Instead, the skill informs the user with an actionable message. For example, if Opus is unavailable when verification is attempted:

  > *"Opus is required for verification but is currently unavailable. Please try again when Opus access is restored, or explicitly request Sonnet-based verification if you accept reduced accuracy."*

  The user must explicitly choose to proceed with a lower tier. Automatic silent fallback is a deliberate non-feature: silently downgrading verification quality could produce misleading compliance results.

### Soft Dependencies (Recommended, Not Required)

- **Python 3**: Used by two verification tools:
  - `tools/verify_report.py` — assembles JSON fragments into a deterministic markdown report
  - `tools/wait_for_done.py` — polls for sub-agent completion markers

  Python 3 is a **soft dependency** — assumed available in the environment (standard on macOS and Linux). If Python 3 is absent, these tools cannot run; the skill falls back to orchestrator-managed alternatives: manual fragment assembly and orchestrator-driven polling loops. See §9.3 for the consistent framing of this assumption.

- **Git**: Strongly recommended for version control of trackers and implementation state, but not required. Worktree support assumes git is available; without it, concurrent sessions require manual directory management.

---

## §9.2 Design Constraints

### Context Window is the Fundamental Constraint

Everything in the skill's architecture — from tracker format to verification pipeline — is shaped by context window limitations and Claude's compaction behavior.

- **Persistent state via markdown files, not conversation memory**: Trackers, verification reports, and preferences live on disk because conversation context is transient. Context compaction loses conversation history; disk state survives.

- **Section references as stable anchors**: Specs are strongly recommended to use numbered section references (§2.1, §3.4) or unambiguous prose headings because these survive context compaction; conversational references ("the part about authentication") do not. Section references are not required — the skill degrades gracefully without them (verification produces coarser-grained results, and V-item matching uses text similarity as a fallback) — but structured §N.M references produce the most reliable outcomes.

- **Structured output over conversational answers**: Sub-agents write JSON fragments to disk, not conversational summaries (NFR-DET-03: "model produces structured data → tool assembles deterministically → model reasons over results"). This is intentional and necessary.

- **Skill restructuring for efficiency**: SKILL.md itself was reduced from ~1400 to ~296 lines in February 2026 specifically to manage context overhead. Large prompt files are broken into reference materials loaded on-demand per phase.

### File-Based State Interchange

The skill uses markdown and JSON files as its primary data interchange format:

- **Trackers**: Markdown with structured field markers (`**Field**:`) and matrix tables
- **Verification fragments**: JSON with requirement ID, status, findings, evidence
- **Preferences**: Markdown with simple key-value pairs

This choice prioritizes human readability and git-friendly diffs over binary serialization.

### Markdown as Spec Format

The skill works with markdown specifications. It does *not* parse:
- YAML spec files
- JSON schemas
- Confluence/Jira exports
- Docx, PDF, or proprietary formats

If source specifications exist in other formats, they must be converted to markdown first (that is outside this skill's scope — the `/spec` skill is responsible for initial spec creation).

### No Explicit Retry Logic for Sub-Agent Failures

When a sub-agent (verification agent, implementation agent, test writer) fails or returns unexpected output:
- There is no built-in retry mechanism
- The skill relies on Claude's natural tendency to self-correct in follow-up attempts
- Users can manually re-run verification or re-assign implementation tasks

This is a practical trade-off to keep skill complexity low; explicit retry logic adds significant overhead.

---

## §9.3 Assumptions

### Specification Pre-Requisites

- **Specifications are pre-written**: The `/implement` skill *consumes* finished specifications; it does not write them. The `/spec` skill is responsible for specification authoring. Users are assumed to arrive with a completed (or near-complete) spec document.

- **Specifications have discrete, testable requirements**: Specs work best when they articulate individual requirements as "must," "should," or "could" statements rather than prose paragraphs. The skill's verification phase depends on being able to extract and verify discrete requirements.

- **Section references are helpful but not mandatory**: Specs with numbered sections (§1.2, §3.4) and unambiguous prose headings work best. The skill degrades gracefully without them—section references are strong anchors, but the skill can still parse and verify unstructured prose, with reduced precision.

### User Environment

- **Python 3 is assumed available** (soft dependency — standard on macOS and Linux): The deterministic verification tools (`tools/verify_report.py`, `tools/wait_for_done.py`) require Python 3. If Python 3 is not present, the skill falls back to orchestrator-managed alternatives (manual fragment assembly, orchestrator-driven polling loops) — see §9.1 for the full degradation behaviour.

- **Git is available** (or user manages concurrent sessions manually): Worktree support was added in February 2026 to handle concurrent sessions across multiple branches. Without git, users must manually segregate working directories and update tracker paths. See §8.5.3 for the skill's behaviour when git is unavailable at runtime.

- **Users understand implementation workflows**: Users are assumed to be familiar with either TDD or traditional implementation patterns, and can meaningfully review and validate tests that verify spec requirements. Note: the TDD sub-agent (§3.2.3) writes the tests from scratch — this assumption is about the user's ability to evaluate whether the generated tests correctly represent the spec intent, not about the user writing tests themselves.

### Skill Behavior Assumptions

- **Users will read the tracker**: The tracker is the source of truth during recovery after context compaction. The skill assumes users will read it and follow its recovery instructions rather than relying on conversational cues.

- **Tests are run after every implementation**: The skill's verification pipeline assumes that tests have been run and pass. Implementation without passing tests is treated as incomplete.

- **Users will approve plans before implementation**: Phase 1 produces a plan (tasks, task order, scope summary) that MUST be approved before Phase 2 begins. The skill assumes this gate is not bypassed.

---

## §9.4 Out of Scope

### Specification Authoring

- **No spec writing**: The `/implement` skill does not write or author specifications. It takes finished specifications as input. If your spec needs to be written or significantly revised, use the `/spec` skill first.

### Deployment & Infrastructure

- **No code deployment**: The skill stops at "implementation complete with tests passing." It does not:
  - Push code to production
  - Deploy infrastructure
  - Run deployment pipelines
  - Update live services

- **No CI/CD pipeline integration**: The skill cannot:
  - Trigger Jenkins, GitHub Actions, or other CI systems
  - Hook into automated test runners
  - Consume pipeline outputs or feedback loops
  - Push code to remote repositories (users can do this manually after verification)

- **No infrastructure-as-code generation**: Infrastructure tooling (Terraform, CloudFormation, Kubernetes manifests) is out of scope. The skill focuses on application code implementation.

### Project Management Integration

- **No Jira, GitHub Issues, or other PM tool integration**: The skill does not:
  - Create or update tickets
  - Sync with project management systems
  - Consume requirements from PM tools
  - Report progress back to PM systems

- **No team workflow management**: No Slack notifications, no calendar blocking, no standup generation.

### Code Quality & Non-Functional Aspects

- **Limited quality checks**: The skill performs spec-compliance verification but does *not* include:
  - Deep code reviews (style, architecture, design patterns)
  - Security vulnerability scanning
  - Performance profiling or optimization
  - Accessibility compliance checks
  - Documentation generation beyond what specs require

  **Rationale**: The primary focus is requirement-to-implementation fidelity, not code quality. Code quality should be managed by separate linting, testing, and review workflows outside this skill.

- **No refactoring**: While the skill *can* be used for refactoring work (and has been in practice), it is not optimized for it. Refactoring typically requires a different workflow (iterative improvement with optional requirements) rather than the requirement-driven model this skill assumes.

### Concurrent Version Management

- **Limited concurrent session support**: The skill has basic worktree support (added Feb 2026) but does not manage:
  - Automatic merge of concurrent changes
  - Conflict resolution
  - Branch synchronization

  Users are responsible for git branching strategy and merging parallel work.

### Web Version Maintenance

- **claude-web/ is not actively maintained**: A web adaptation exists in the repository but is stale and not part of the active skill roadmap. The CLI version (skills/implement/) is canonical.

---

## §9.5 Future Considerations

### Claude Code Version Resilience

**Current state**: No hard version constraints on Claude Code CLI; the skill uses platform features (Task tool, TaskCreate/Update, background agents) that could change in future versions.

**Future**: Consider pinning minimum Claude Code versions if the platform makes breaking changes to Task tool semantics or sub-agent spawning.

### CI/CD Hook Points

**Current state**: No pipeline integration.

**Future**: Could add optional integration points:
- Consume spec changes from a GitHub branch
- Push verified implementation to a PR
- Trigger verification on code review
- Report verification results back to GitHub

This would require careful design to avoid over-coupling the skill to CI/CD services.

### Web Version Revival

**Current state**: `claude-web/` directory exists but is not actively maintained. The web-based Claude interface does not support Task tool or sub-agent spawning, making full skill replication impossible.

**Future**: If web Claude gains Task tool support, could revive and align the web version with the CLI version.

### Quality Gate Extensibility

**Current state**: Limited quality checks; focus is spec compliance.

**Future**: Could add optional gate for:
- Linting checks (Python flake8, JavaScript ESLint, etc.)
- Type checking (mypy, TypeScript, etc.)
- Basic security scans
- Test coverage thresholds

These would be opt-in to keep the skill focused; users with strict quality requirements can layer them on top.

### Specification Evolution During Implementation

**Current state**: Basic spec freshness detection exists (§8.4 edge cases); no full merge/diff logic.

**Future**: Could add:
- Automatic spec-to-tracker reconciliation when specs change mid-implementation
- Diff-based notification of requirement changes
- Interactive conflict resolution (old requirement changed? remove, add new, or modify implementation?)

### Parallel Verification Optimization

**Current state**: Parallel sub-agents work well at scale (documented scale: 20-40+ agents, several thousand requirements).

**Future**: Could optimize further with:
- Automatic batching of small requirements (group 5-10 small reqs into one agent) — **note**: this would require relaxing FR-3.15, which currently mandates one verification agent per requirement. Any batching proposal must explicitly amend that rule rather than working around it.
- Smarter model tier routing (very simple reqs → Haiku always, complex edge cases → Opus)
- Caching of frequently-verified requirements (edge cases, common patterns)

---

## Summary

The `/implement` skill is fundamentally constrained by context windows, model tier availability, and the need for persistent disk-based state. It assumes specifications are pre-written, Python 3 and git are available (soft dependencies with graceful degradation if absent), and users will follow the planning → implementation → verification workflow. Model tier selection is quality-critical — there is no silent automatic fallback; if a tier is unavailable, the skill informs the user and requires an explicit choice to proceed at reduced accuracy. Section references are strongly recommended but not required; the skill degrades gracefully without them. It deliberately excludes spec authoring, deployment, CI/CD, and deep code quality work. Future evolution should focus on version resilience, optional CI/CD hooks, and quality gate extensibility while maintaining the skill's core identity as a specification-fidelity tool.
