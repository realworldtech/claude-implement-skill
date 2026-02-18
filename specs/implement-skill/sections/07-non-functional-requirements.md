# §7 Non-Functional Requirements

> Part of [Master Spec](../spec.md)

---

Non-functional requirements govern how the `/implement` skill performs across dimensions that are orthogonal to individual features: how efficiently it uses context, how much it costs to run, how well it scales, how reliably it recovers from failure, and how predictably its assembly pipeline behaves. These requirements are not aspirational — they are structural constraints that shaped the skill's architecture from the ground up.

---

## §7.1 Context Window Efficiency

### NFR-CTX-01: Skill entry point MUST fit within a minimal context budget

**Requirement:** The skill's primary entry point (`SKILL.md`) MUST be structured so that loading it does not consume a disproportionate share of the orchestrator's context window. Phase reference files MUST be loaded on demand, not pre-loaded in full at skill activation. `SKILL.md` SHOULD remain under 400 lines (approximately 12,000–16,000 tokens at typical prose density). Growth beyond this threshold indicates the file needs restructuring.

**Rationale:** The orchestrator's context window is the primary resource constraint in long implementation sessions. A skill that loads thousands of lines of reference material at startup leaves less room for specification content, implementation status, and developer interaction — the things that actually matter. Bloated skill files also increase the risk of the orchestrator itself suffering from the U-shaped attention degradation documented in §1.1.

**How the skill meets it:** `SKILL.md` was restructured from approximately 1,400 lines to approximately 296 lines as a deliberate context optimisation. Phase reference files (planning, implementation, verification, etc.) are referenced by path and loaded only when the relevant phase begins. The skill's own structure embodies the principle it enforces for specifications.

---

### NFR-CTX-02: Sub-agents MUST write structured output to disk, not return conversational responses

**Requirement:** Sub-agents MUST write their results as structured artefacts to disk (e.g., JSON summary files, `.done` markers, verification fragments). The orchestrator reads these artefacts from disk rather than parsing the sub-agent's conversational reply.

**Rationale:** Conversational sub-agent responses flow back into the orchestrator's context window, consuming tokens for content the orchestrator may only need to sample lightly (e.g., "did it succeed? any concerns?"). Structured artefacts on disk allow the orchestrator to read targeted fields — `status`, `concerns`, `digest` — without ingesting the full agent reply.

**How the skill meets it:** All sub-agent prompt templates instruct the agent to write a structured `summary.json` to `.impl-work/<spec-name>/summary.json` and to place a `.done` marker when complete. The orchestrator reads these files directly; it does not rely on the agent's conversational output for decision-making.

---

### NFR-CTX-03: Parallel heavy-context phases MUST be limited to two concurrent draft agents

**Requirement:** Implementation sub-agents MUST NOT exceed 2 concurrent heavy agents (sonnet or opus tier). Verification sub-agents are exempt from this cap — they are lightweight, uniform, and dispatched in parallel by design.

**Rationale:** Each sub-agent spawned consumes model capacity with a full context load. Spawning many heavy-context agents simultaneously provides diminishing throughput returns while increasing the risk of resource contention and degraded output quality. Verification agents operate on a per-requirement basis with much smaller context loads and are structured for safe parallelism.

**How the skill meets it:** Orchestrator guidance in the planning phase caps concurrent draft agents at two for large-section work. Verification agents may be parallelised freely up to platform limits (see §7.3).

---

### NFR-CTX-04: The tracker file MUST maintain a minimal token footprint while preserving recoverability

**Requirement:** The implementation tracker file MUST encode all state needed for session recovery in a compact, structured format. It MUST NOT accumulate unbounded content (e.g., full implementation notes, code excerpts, or verbose logs) that would make it expensive to load at the start of every orchestrator action.

**Rationale:** The tracker is read at the beginning of every orchestrator decision cycle. If it grows without bound, it imposes an ever-increasing context tax on every step of the workflow. At the same time, it must contain enough information for full recovery after context compaction — a tension that demands careful structural discipline.

**How the skill meets it:** The tracker uses a fixed-schema table format for requirement status, section references, and phase state. Free-text fields are bounded: Implementation Log entries SHOULD NOT exceed 200 words; the Specification Summary SHOULD NOT exceed 500 words. These are advisory targets rather than enforced limits, but consistent compliance is expected to prevent tracker growth from imposing context overhead. The schema is designed to convey maximum recovery information in minimum tokens: a structured table row encodes requirement ID, status, section reference, and any blocking issue in a single line.

---

## §7.2 Cost Management

### NFR-COST-01: The skill MUST apply model tiering based on task complexity

**Requirement:** The skill MUST select model tier based on task characteristics. Haiku or Sonnet MUST be used for boilerplate and routine tasks. Sonnet MUST be used for standard implementation. Opus MUST be used for verification, gap fixing, and complex reasoning tasks.

**Rationale:** Opus is the most capable and most expensive tier. Applying it uniformly across all sub-agent tasks would make the skill economically impractical for real-world projects with hundreds of requirements. Conversely, using cheaper models for verification risks missing subtle specification violations — which defeats the skill's entire purpose. Model selection must be a function of where correctness risk is highest.

**How the skill meets it:** The sub-agent strategy reference defines explicit routing rules:

| Task | Model |
|------|-------|
| Boilerplate, simple CRUD, adding fields | Haiku or Sonnet |
| Standard implementation | Sonnet |
| Verification | Opus (always) |
| Gap fixing | Opus (always) |
| Logic decisions, algorithmic work, state management | Opus |

These rules are enforced in the orchestrator guidance, not left to discretion.

---

### NFR-COST-02: Large-spec routing MUST tier model selection by section size

**Requirement:** When a specification has breakout section files, the orchestrator MUST build a structural index by measuring section file sizes and route implementation sub-agents by estimated token count. Sections below 5,000 tokens MAY be grouped two to three per agent using Sonnet. Sections between 5,000 and 20,000 tokens MUST use one Sonnet agent per section. Sections above 20,000 tokens MUST use Opus.

**Rationale:** Section size is a proxy for complexity and context load. Grouping small sections reduces agent dispatch overhead and cost. Large sections warrant Opus not just because they are expensive to process, but because longer sections are more likely to encode complex interactions, cross-cutting constraints, and edge cases where cheaper models produce incomplete implementations.

**How the skill meets it:** The sub-agent delegation strategy reference (`skills/implement/references/sub-agent-strategy.md`) specifies this routing table explicitly. The orchestrator evaluates section sizes during the planning phase and records routing decisions in the tracker.

---

### NFR-COST-03: Sonnet agents MUST support DIGEST-based escalation to Opus

**Requirement:** Sonnet implementation agents MUST include a `digest` field in their structured summary output. The orchestrator MUST evaluate this digest against a complexity category table. When a match is found, Opus re-review of that agent's output is MANDATORY and non-discretionary. See §5.4.2 for the canonical complexity category table and signal keywords. See also §6.5 for how DIGEST escalation integrates with the implementation sub-agent workflow.

"Opus re-review" means the opus agent reviews the sonnet agent's code changes and findings, focusing on the complexity area identified by the DIGEST signal. See §5.4.3 for the operational procedure.

**Rationale:** The size-based routing in NFR-COST-02 is a heuristic. It will sometimes send moderately complex work to Sonnet that turns out to involve algorithmic subtleties, state machine interactions, or security-boundary logic. DIGEST-based escalation provides a runtime correction mechanism: the agent itself signals when it encountered something that warrants higher-model review.

**How the skill meets it:** Complexity categories that trigger mandatory escalation include: algorithm/calculation/formula logic, state machine transitions, permission and access control, complex conditional business rules, and cross-cutting system-wide constraints. When any of these appear in the `digest` field, the orchestrator dispatches an Opus review agent without rationalisation or override.

---

## §7.3 Scalability

### NFR-SCALE-01: The skill MUST remain effective for specifications with thousands of requirements

**Requirement:** The skill's methodology MUST not degrade in correctness or completeness as specification size increases from tens to thousands of requirements. It MUST NOT require the full specification to be loaded into any single context window.

**Rationale:** Real-world project specifications in active use by this skill reach several thousand requirements. This is not a theoretical limit — it is an observed usage pattern. Any design that requires the entire specification to be in context simultaneously would be fundamentally unscalable.

**How the skill meets it:** The per-requirement verification model (NFR-SCALE-02), structural indexing for large multi-file specs, and the section-reference anchoring system collectively ensure that no single agent, orchestrator action, or tool invocation requires loading the full specification. Each unit of work operates on the minimum specification context needed to perform that unit.

---

### NFR-SCALE-02: Verification MUST scale linearly via per-requirement parallelism

**Requirement:** The verification phase MUST dispatch one sub-agent per requirement. The total verification throughput MUST scale linearly with the number of parallel agents the platform supports. For medium-sized specifications, the expected parallelism is 20 to 40 or more concurrent verification agents.

**Rationale:** Batching multiple requirements per verification agent was empirically found to produce less thorough results than one agent per requirement (see §1.5, Iteration 8). Single-requirement agents also scale more predictably: the total verification time is approximately the time for one agent, bounded by platform parallelism limits, rather than growing with specification size.

**How the skill meets it:** Each verification agent receives exactly one requirement ID, the relevant specification section text, and a pointer to the implementation under test. Agents write JSON result fragments to `.impl-verification/fragments/<req-id>.json`. The Python tool `verify_report.py` assembles these fragments deterministically after all agents complete.

---

### NFR-SCALE-03: Structural indexing MUST be used for large multi-file specifications

**Requirement:** For specifications with breakout section files, the orchestrator MUST build a structural index (section IDs, file paths, estimated token sizes) before beginning implementation. This index MUST be used to route work without loading full section content into the orchestrator's context.

**Rationale:** Loading every section of a large specification into the orchestrator to decide which section to work on next is a self-defeating strategy: it consumes exactly the context that needs to be preserved for implementation. Structural indexing allows the orchestrator to reason about the specification's shape without ingesting its substance.

**How the skill meets it:** The planning phase instructs the orchestrator to run `wc -c` across section files, build a routing table, and record it in the tracker. Section content is loaded by sub-agents only when that section is the active work item.

---

## §7.4 Reliability and Recovery

### NFR-REL-01: The tracker MUST be self-recovering after context compaction

**Requirement:** The tracker file MUST contain embedded recovery instructions sufficient for the orchestrator to reconstruct sufficient session state for resumption after a context compaction event or session restart, without developer intervention.

**Rationale:** Context compaction is not an exceptional failure mode — it is an expected event in any sufficiently long implementation session. A skill that requires developer intervention to recover from compaction imposes an operational burden that undermines its value proposition. The tracker must make recovery automatic.

**How the skill meets it:** The tracker file opens with an explicit "Recovery Instructions" section as the first substantive content block. These instructions tell a freshly-loaded orchestrator, in priority order: what phase it is in, what to read to reconstruct state, and what not to do (e.g., do not begin from scratch, do not start implementation in the orchestrator directly). The tracker's structure is designed so that reading it alone is sufficient to resume work.

---

### NFR-REL-02: The TaskList MUST survive context compaction

**Requirement:** Implementation task progress MUST be recorded in a mechanism that survives context compaction events and is visible to a freshly-loaded orchestrator without file I/O.

**Rationale:** The orchestrator's in-context task list evaporates on compaction. If task progress is only tracked in the conversation, a compaction event requires the orchestrator to reconstruct which tasks were done and which remain — a fallible process that risks re-doing completed work or skipping incomplete work.

**How the skill meets it:** The skill uses the Claude Code `TaskList` facility, which persists independently of conversation context and is surfaced to a new conversation automatically. The tracker recovery instructions include an explicit step to run `TaskList` to see task-level progress.

**Dependency note:** This requirement depends on Claude Code's TaskList facility persisting across context compaction. If TaskList does not survive compaction, the tracker file alone MUST be sufficient for recovery — the Recovery Instructions section is designed for this fallback.

---

### NFR-REL-03: Sub-agent completion MUST use a `.done` marker polling pattern

**Requirement:** Sub-agent completion MUST be signalled via a `.done` marker file written by the agent when its work is finished. The orchestrator MUST use `wait_for_done.py` to poll for these markers rather than relying on the agent's conversational return.

**Rationale:** Conversational return signals are unreliable for coordinating parallel sub-agents — there is no guarantee that all agents have finished before the orchestrator attempts to assemble results. Marker file polling provides a deterministic synchronisation point that is independent of conversation turn ordering.

**How the skill meets it:** All sub-agent prompt templates include an instruction to write a `.done` file to a specified path as the final step. `wait_for_done.py` polls for the presence of all expected marker files before signalling to the orchestrator that assembly can begin.

**Failure response:** If a sub-agent fails to write a `.done` marker within the timeout period, the orchestrator MUST log the failure and report which agents did not complete. The orchestrator SHOULD continue with available results rather than blocking indefinitely. The orchestrator MUST NOT retry automatically — the user must be informed and can choose to re-dispatch.

---

### NFR-REL-04: Session resume MUST include spec freshness and worktree validation

**Requirement:** On `/implement continue`, the orchestrator MUST verify that the specification has not changed since the tracker was last updated. For worktree-based implementations, the orchestrator MUST verify that the expected worktree exists and is on the correct branch before resuming.

**Rationale:** Resuming an implementation session against a modified specification without acknowledgement risks producing implementation that satisfies an outdated requirement set. Similarly, resuming in the wrong worktree can corrupt work across concurrent feature branches.

**How the skill meets it:** The continue phase includes an explicit spec freshness check and a worktree validation step. If either check fails, the orchestrator surfaces the discrepancy to the developer before proceeding. For single-file specs, freshness is checked by comparing the file's modification timestamp (mtime) against the `**Spec Baseline**` date recorded in the tracker (FR-5.6). For multi-file specs, freshness is checked by comparing current byte counts against the structural index stored in the tracker (§8.4.1). Hash-based change detection is not implemented.

---

## §7.5 Deterministic Processing

### NFR-DET-01: Report assembly MUST be performed by deterministic tools, not LLM inference

**Requirement:** The assembly of verification results from sub-agent output fragments into a final verification report MUST be performed by a deterministic Python script (`verify_report.py`), not by an LLM. The LLM's role is to reason over the assembled report, not to assemble it.

**Rationale:** LLM-based assembly of structured data introduces hallucination risk — the model may invent summary statistics, misattribute failures to requirements, or silently omit fragments it finds ambiguous. For a verification system whose purpose is to detect specification violations with high fidelity, hallucination in the assembly step would be catastrophic. Deterministic tools eliminate this risk entirely.

**How the skill meets it:** `verify_report.py` reads all JSON fragment files from `.impl-verification/fragments/`, validates their schema, computes pass/fail/skip counts, calculates delta from the previous run, and writes a structured report. None of these steps involve LLM inference. The orchestrator reads the assembled report and provides interpretation to the developer.

---

### NFR-DET-02: Polling and coordination MUST use deterministic tooling

**Requirement:** All polling, synchronisation, and coordination operations in the verification pipeline MUST be implemented as deterministic Python scripts. LLM inference MUST NOT be used for these operations.

**Rationale:** The same principle that applies to assembly (NFR-DET-01) applies to coordination: LLMs should not be used to perform tasks that are better expressed as deterministic algorithms. Polling for file existence, counting completed agents, and computing deltas are all mechanical operations with no ambiguity — they are the domain of code, not inference.

**How the skill meets it:** `wait_for_done.py` handles all polling and completion detection. It reads the filesystem state, checks for expected marker files, and returns a deterministic status. The orchestrator invokes it as a tool and acts on its output without LLM reinterpretation of the raw filesystem state.

---

### NFR-DET-03: The core pipeline pattern MUST be "model produces structured data → tool assembles → model reasons"

**Requirement:** All verification and report assembly pipelines MUST follow the model→tool→model sequence: (1) sub-agent models produce structured data written to disk; (2) deterministic tools assemble, aggregate, or transform that data; (3) the orchestrator model reasons over the assembled result. Steps 1 and 3 involve LLM inference; step 2 MUST NOT. This pattern applies specifically to verification and report assembly — not to all orchestration steps in the skill.

**Rationale:** This three-step separation provides a hard boundary that prevents LLM inference from contaminating assembly operations. It also makes the pipeline auditable: the output of step 2 is a deterministic, inspectable artefact that the developer can examine independently. Any discrepancy between what sub-agents produced and what the orchestrator reported becomes traceable to a specific file rather than hidden inside a model's reasoning process.

**How the skill meets it:** This pattern is stated as an explicit core design principle in the skill's architecture references and is implemented end-to-end in the verification pipeline. The verification workflow is structured around this model → tool → model sequence.

---

## §7.6 Security

### NFR-SEC-01: The skill MUST NOT write secrets or credentials to disk artefacts

**Requirement:** Tracker files, verification fragments, summary JSON files, and `.done` markers MUST NOT contain API keys, passwords, tokens, or other credentials. Sub-agent task briefs MUST NOT include secrets even if the specification under implementation references secrets management. The skill operates only on specification content and code structure, not on live credentials.

**Rationale:** Artefacts written by the skill (trackers, fragments, summaries) are git-committed alongside implementation code by many users. A tracker or fragment that inadvertently captures a secret from a specification would expose that secret in version control history.

**How the skill meets it:** Sub-agent prompt templates are scoped to specification content and code artefacts. They do not request or surface runtime environment values. Users are responsible for ensuring their specifications do not embed live credentials — the skill does not validate this, but it does not propagate such content into its own artefact schema.
