# Pathfinder v2 — Proposal

> Architecture knowledge layer for LLM agents: auto-discover, selectively load, visually validate, and enforce component boundaries.

**Authors:** CYD Team
**Date:** 2026-04-09
**Status:** Draft
**Context:** Learnings from pathfinder v1 brownfield discovery on ChatYourData (74 components, 30 flows, ~60 CLI calls, multiple CLI bugs)

---

## 1. Problem Statement

LLM agents working on large codebases need architectural knowledge to make correct decisions. Today there are two extremes:

| Approach | Pros | Cons |
|----------|------|------|
| **CLAUDE.md** (prose) | Zero-cost loading, rich operational context, human-maintained | All-or-nothing (full file every session), scales poorly past ~4K tokens, goes stale silently, not queryable |
| **Pathfinder v1** (structural graph) | Queryable, exportable, validatable | High setup cost (60+ CLI calls), each query is a tool call, no operational knowledge, CLI ergonomics issues |

Neither alone is sufficient. Both fail at the core need: **load the right architectural knowledge at the right time with minimal token overhead.**

Additionally, neither provides a fast way for the **human** to validate the agent's understanding — the human must read prose or raw component lists, not see a visual representation.

---

## 2. Prior Art & Landscape

Research and existing tools confirm this is an active problem space with no complete solution yet.

### 2.1 Closest Matches

**[Repository Intelligence Graph (RIG)](https://arxiv.org/abs/2601.10112)** — Academic paper (Jan 2026). Builds a deterministic architectural map from build/test artifacts (CMake). The SPADE extractor produces an LLM-friendly JSON graph of buildable components, dependencies, tests, and external packages. Tested with Claude Code, Cursor, and Codex — improved accuracy by 12.2% and reduced completion time by 53.9%. **Limitation:** Only extracts build structure, not data flows or logical component boundaries. CMake-only currently.

**[Codified Context](https://arxiv.org/abs/2602.20478)** — Academic paper (Feb 2026). Defines a three-layer infrastructure for AI agents: (1) hot-memory constitution (conventions), (2) specialized domain-expert agents, (3) cold-memory knowledge base (on-demand specs). Built with Claude Code across 283 sessions on a 108K-line C# system. **Key insight:** Over half of each spec's content is project-domain knowledge (codebase facts, patterns, failure modes), not behavioral instructions. **Closest to our Layer 1+3 concept.**

**[codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp)** — Open source MCP server. Parses codebases into a persistent knowledge graph using tree-sitter (66 languages). 14 MCP tools including `search_graph`, `trace_call_path`, `get_architecture`. Achieves 99.2% token reduction vs file-by-file exploration. Indexes Linux kernel (28M lines) in 3 minutes. **Limitation:** Indexes code structure (functions, classes, imports, call chains) but has no concept of architectural boundaries, data flows, or component ownership. It's a query backend, not an architecture tool.

**[Structurizr + C4 Model](https://structurizr.com/)** — Architecture-as-code using Structurizr DSL. Now has an [MCP server](https://github.com/structurizr) for AI agent integration. LLM agents can parse and generate C4 models. Research shows [multi-agent C4 generation](https://arxiv.org/abs/2510.22787) is feasible. **Limitation:** Requires manual DSL authoring (no auto-discovery from code). Designed for human architects, not LLM consumption.

### 2.2 Partial Overlaps

**[Swark](https://github.com/swark-io/swark)** — VS Code extension that auto-generates Mermaid architecture diagrams from code using LLMs (via Copilot API). Sends code files as prompt context, LLM infers component structure. **Limitation:** One-shot diagram generation, no persistent graph, no boundary enforcement, non-deterministic (LLM does all inference).

**[Aider repo-map](https://aider.chat/) / [RepoMapper MCP](https://mcpservers.org/servers/pdavis68/RepoMapper)** — Builds a ranked map of code elements using tree-sitter + PageRank. Helps LLMs find relevant code efficiently. **Limitation:** File/function-level, not architectural. No components, boundaries, or flows.

**[graphify](https://github.com/safishamsi/graphify)** — Claude Code skill that turns code into a queryable knowledge graph. Claims 71.5x fewer tokens per query. **Limitation:** Similar to codebase-memory-mcp — structural code graph, not architectural.

**Architecture Fitness Functions ([ArchUnit](https://www.archunit.org/), [Dependency-Cruiser](https://github.com/nicedoc/dependency-cruiser))** — Enforce architectural rules as executable tests. ArchUnit (Java) tests package dependencies, naming conventions, class relationships. Dependency-Cruiser (JS/TS) validates import rules. Emerging work on [LLM-generated fitness functions from ADL](https://lukasniessen.medium.com/fitness-functions-automating-your-architecture-decisions-08b2fe4e5f34). **Limitation:** Rule-based, not graph-based. Must be manually written. No LLM integration yet (only LLM generation of rules).

**[Augment Code Context Engine](https://www.augmentcode.com/)** — Commercial tool using semantic dependency analysis to build a graph of codebase architecture across repositories. **Limitation:** Proprietary, cloud-hosted, not self-hostable or customizable.

### 2.3 Research & Ideas

**[Toward Architecture-Aware Evaluation Metrics for LLM Agents](https://arxiv.org/abs/2601.19583)** — Proposes metrics for evaluating whether LLM agents respect architectural constraints. Confirms the problem space is recognized academically.

**Token waste is quantified:** [Multiple sources](https://medium.com/@jakenesler/context-compression-to-reduce-llm-costs-and-frequency-of-hitting-limits-e11d43a26589) report that 60-80% of tokens consumed by AI coding agents go toward figuring out where things are, not answering the actual question.

**[AI-Assisted C4 from Code](https://www.workingsoftware.dev/ai-assisted-software-architecture-generating-the-c4-model-and-views-directly-from-code/)** — Practical guide for using Claude Code to analyze codebases and generate Structurizr DSL. Manual but demonstrates the workflow.

### 2.4 Gaps — What Doesn't Exist Yet

| Capability | Exists? | Closest |
|-----------|---------|---------|
| Auto-discover components from code | Partial | Swark (LLM-inferred), RIG (build-system only) |
| Persistent queryable component graph | Yes | codebase-memory-mcp, but code-level not architecture-level |
| Data flow modeling between components | No | — |
| Boundary enforcement / drift detection | Partial | ArchUnit/Dep-Cruiser (manual rules), no LLM integration |
| Token-efficient task-scoped context | No | Codified Context (manual specs), not compiled from graph |
| Visual diagram for human validation | Partial | Swark (one-shot), Structurizr (manual DSL) |
| Integrated discover + query + enforce + view | **No** | — |

**The gap pathfinder v2 fills: an integrated tool that auto-discovers architecture, maintains it as a queryable graph, compiles task-scoped context, generates validation diagrams, and enforces boundaries — designed for LLM agent consumption, not human architects.**

---

## 3. Design Principles

1. **Token efficiency above all.** Every token in context that isn't relevant to the current task is waste.
2. **Auto-derive structure, manually confirm boundaries.** The graph should bootstrap from code. Humans correct it, not create it.
3. **Visual validation loop.** Humans validate architecture understanding through diagrams, not by reading YAML.
4. **Guardrails over documentation.** Preventing violations is more valuable than describing the architecture.
5. **Integrated, not bolted on.** Architecture knowledge should be part of the agent's workflow, not a separate CLI tool.

---

## 4. Four Knowledge Layers

### Layer 1: Conventions (CLAUDE.md)
**What:** Coding rules, security mandates, build commands, naming patterns.
**Maintained by:** Humans.
**Loaded:** Auto-injected every session (keep lean — conventions only, no architecture prose).
**Changes rarely.** ~500-1000 tokens max.

### Layer 2: Structure (Pathfinder graph)
**What:** Components, ownership, flows, code mappings, external systems.
**Maintained by:** Auto-derived from code + human-confirmed boundaries.
**Loaded:** On demand, sliced by task.
**Changes when code changes.** Validated continuously.

### Layer 3: Task Context (compiled on demand)
**What:** The intersection of Layer 1 + Layer 2 relevant to the current task.
**Maintained by:** Generated, not stored.
**Loaded:** Once at task start.
**Disposable.** ~200-500 tokens.

### Layer 4: Embedded Viewing (visual validation)
**What:** Token-efficient diagrams (SVG/Mermaid) of flows, boundaries, and component relationships.
**Purpose:** Human validates agent's understanding, catches misclassifications, corrects boundaries.
**Generated on demand.** Supports iterative refinement ("OpenAPI should be a datasource, not a service").

---

## 5. Proposed API

Replace 25+ CLI commands with a semantic API designed for LLM consumption.

### 5.1 Context Loading

```
pathfinder context <task-description>
```

Returns a focused document combining:
- Relevant components and their relationships
- Data flows in the affected area
- Code file ownership
- Applicable conventions from CLAUDE.md
- Known constraints and boundaries

**Example:**
```bash
$ pathfinder context "fix SQS parsing in GAIA job processor"

# Context: GAIA Job Processing
Components: gaia/job-processor, gaia/message-gateway, prozess-request/strategy
Flows:
  ext/gaia --> api-layer/gaia [POST /gaia/{id}]
  api-layer/gaia --> gaia/job-processor [SQS: gaia-job-queue]
  gaia/job-processor --> prozess-request/strategy [Lambda invoke]
  gaia/job-processor --> gaia/message-gateway [SQS result]
  gaia/message-gateway --> ext/gaia [ToolsSDK.send_message]
Files:
  api/external/gaia_job_processor/code/lambda_function.py
  api/external/gaia_message_gateway/code/lambda_function.py
Conventions:
  - Use log_event_safely() for all event logging
  - Lambda handler signature: lambda_handler(event, context)
```

Single call. ~300 tokens. Everything the agent needs.

**Implementation options:**
- (a) **File-path matching** — if user mentions a file, resolve its component from code mapping, BFS 1-2 hops for related components. Works today with existing graph. **LOW effort.**
- (b) **Keyword-to-component matching** — map task keywords to component names/specs. **MEDIUM effort.**
- (c) **LLM-assisted task parsing** — ask an LLM to identify relevant components from the task description. More accurate, higher latency. **MEDIUM-HIGH effort.**

**Recommendation:** Start with (a), add (b) as enhancement. Skip (c) — it costs the tokens we're trying to save.

### 5.2 Impact Analysis

```
pathfinder impact <file-or-component>
```

Returns what depends on this component, what it depends on, and what flows through it.

**Implementation complexity: LOW.** Pure graph traversal on existing pathfinder data. Combine existing `dependents`/`deps`/`trace` commands into one output.

### 5.3 Boundary Check

```
pathfinder check [--files <changed-files>]
```

Validates that code changes respect component boundaries. Reports new imports that cross undeclared boundaries, unmapped files, and drift.

**Implementation options:**
- (a) **Regex-based import scanning on git diff** — fast, 80% accurate, misses dynamic imports. **MEDIUM effort.**
- (b) **AST-based with tree-sitter** — accurate, needs per-language parsers. **HIGH effort.** (Note: codebase-memory-mcp already solves this for 66 languages — could reuse their parser)
- (c) **LSP integration** — most accurate, complex setup. **VERY HIGH effort.**
- (d) **Hybrid:** Regex on diff for CI, tree-sitter for deep analysis. **MEDIUM effort.**

**Recommendation:** Start with (a) for immediate value. Evaluate integrating codebase-memory-mcp's tree-sitter parsing for (b) later.

### 5.4 Visual Generation

```
pathfinder view [<component-or-flow>] [--format svg|mermaid]
```

Generates a token-efficient diagram for human validation.

**Modes:**
- `pathfinder view` — full system context diagram
- `pathfinder view gaia` — focused component diagram with its flows
- `pathfinder view --trace frontend prozess-request` — end-to-end flow diagram
- `pathfinder view --externals` — external systems and their touchpoints

**Implementation options:**
- (a) **Mermaid-only** — trivial, renders in any markdown viewer. **LOW effort.**
- (b) **Mermaid + DOT export** — let Graphviz handle layout. **LOW effort.**
- (c) **SVG templates per diagram type** — high quality, labor-intensive. **HIGH effort.**
- (d) **Delegate SVG to LLM agent** — already proven in this session. **Zero tool effort.**

**Recommendation:** (a) Mermaid for quick validation built into the CLI. (d) Delegate full SVG to the agent when higher quality is needed.

---

## 6. Auto-Discovery (Bootstrapping)

### The v1 Problem
Discovery required 60+ manual CLI calls. Unsustainable.

### Lessons from Existing Tools

| Tool | Approach | What it gets right | What it misses |
|------|----------|-------------------|----------------|
| RIG/SPADE | Deterministic extraction from build artifacts | Reliable, evidence-based | Only build structure, not logical boundaries |
| Swark | LLM infers everything from code | Flexible, any language | Non-deterministic, no persistence |
| codebase-memory-mcp | tree-sitter AST + Louvain clustering | Fast, 66 languages, persistent | Code-level not architecture-level |
| Structurizr | Manual DSL | Precise, validated | No auto-discovery |

### v2 Approach: Hybrid — Deterministic Foundation + Human Confirmation

```
pathfinder discover [--root <path>]
```

**Phase 1 — Automatic analysis (deterministic, no LLM needed):**
- Scan directory structure for architectural patterns
- Parse imports with tree-sitter (reuse codebase-memory-mcp approach)
- Detect framework conventions (Lambda handlers, FastAPI routers, Angular modules)
- Identify external system calls (boto3 clients, HTTP clients, DB drivers)
- Read existing CLAUDE.md for naming hints

**Phase 2 — Propose and confirm (visual):**
- Generate a Mermaid diagram of the proposed hierarchy
- Present to human: "Here's what I found. What's wrong?"
- Human corrects via diagram, not YAML
- Apply corrections in one batch

**Phase 3 — Map and validate:**
- Auto-map all source files based on directory ownership
- Flag ambiguous files
- Run `validate`

**Implementation complexity: MEDIUM-HIGH.**

**Recommendation:** Rule-based heuristics for Phase 1 (directories, imports, framework patterns). Mermaid output for Phase 2. One-command batch apply for Phase 3.

---

## 7. Maintaining Structure Over Time

### Option A: Pre-commit Hook (recommended start)

```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: pathfinder-check
      entry: pathfinder check --files
      pass_filenames: true
```

Regex-based import scanning on changed files. Warns on undeclared cross-boundary imports. **LOW effort** once `check` is implemented.

### Option B: CI/CD Integration

Same as Option A but runs in pipeline. Team-wide enforcement. **LOW incremental effort.**

### Option C: Agent-Driven Sync

After significant changes, agent runs `pathfinder sync` to detect new/moved/deleted files and propose graph updates. **MEDIUM effort.**

### Recommendation
Start with **Option A** (pre-commit), evolve to **Option B** (CI/CD). Option C is nice-to-have.

---

## 8. CLI Ergonomics (v1 Bug Fixes)

Must-fix regardless of v2 scope:

| # | Issue | Fix |
|---|-------|-----|
| 1 | `add` has no `--spec` flag | Add `--spec` to `add` for one-command creation |
| 2 | `set` doesn't resolve slash-name IDs | Unify ID resolution across all commands |
| 3 | `map --glob` broken by shell expansion on Windows | Accept directory paths natively |
| 4 | Unicode `->` crashes on Windows cp1252 | Use ASCII or set encoding in CLI |
| 5 | `show` without args fails | Display full tree when no arg given |
| 6 | No `flow-remove` or `flow-update` | Add flow mutation commands |
| 7 | No external component guidance in skill | Document external vs internal |

---

## 9. Implementation Roadmap

### Phase 1: Fix v1 + Quick Wins (1-2 weeks)
- Fix all 7 CLI bugs
- Add `pathfinder view` with Mermaid output
- Add `flow-remove`, `--spec` on `add`
- Update discovery skill to match actual CLI syntax

**Delivers:** Usable v1 with visual validation.

### Phase 2: Context Compiler (2-3 weeks)
- Implement `pathfinder context` (file-path-based component resolution + BFS)
- Implement `pathfinder impact` (graph traversal)
- Convention extraction from CLAUDE.md by component tags

**Delivers:** Token-efficient context loading — the biggest agent productivity gain.

### Phase 3: Auto-Discovery (2-4 weeks)
- Rule-based directory/import scanner for Python + TypeScript + Terraform
- Mermaid diagram proposal for human confirmation
- One-command batch creation

**Delivers:** 5-minute setup instead of 60+ CLI calls.

### Phase 4: Guardrails (2-3 weeks)
- `pathfinder check` with regex-based import scanning
- Pre-commit hook integration
- CI/CD template

**Delivers:** Architecture enforcement.

---

## 10. Potential Integrations

| Tool | Integration Point | Value |
|------|------------------|-------|
| codebase-memory-mcp | Reuse tree-sitter parsing for auto-discovery and boundary checking | Avoid rebuilding 66-language parser |
| Structurizr MCP | Export pathfinder graph as Structurizr DSL for C4 diagrams | Higher-quality diagrams for documentation |
| ArchUnit / Dep-Cruiser | Generate fitness function rules from pathfinder boundaries | Executable architecture tests |
| RIG/SPADE | Import build structure as foundation for component graph | Deterministic build-aware components |

---

## 11. Success Metrics

| Metric | v1 (current) | v2 Target |
|--------|-------------|-----------|
| Setup time (new codebase) | 30-60 min, 60+ CLI calls | < 5 min, 1 command + confirm |
| Tokens per session for orientation | 1000-2000 (exploration) or 4000+ (full CLAUDE.md) | 200-500 (focused context) |
| Human validation time | Read YAML/component list | Glance at diagram |
| Drift detection | Manual (`validate`) | Automatic (CI/pre-commit) |
| Boundary violations caught | 0 (no enforcement) | Flagged before commit |

---

## 12. Open Questions

1. **Should pathfinder own conventions too?** Or keep CLAUDE.md separate? The "Codified Context" paper suggests a unified hot-memory constitution. Merging gives one source of truth; separating keeps concerns clean.

2. **Reuse codebase-memory-mcp?** Its tree-sitter parsing and knowledge graph could be a foundation layer, with pathfinder adding architectural semantics (boundaries, flows, ownership) on top. Evaluate whether integration is practical vs. building from scratch.

3. **Language support priority.** Python is primary. TypeScript (frontend) is secondary. Terraform HCL for infra components. What's the minimum viable set?

4. **Graph storage format.** Current YAML-per-component works but requires index rebuild. Consider SQLite (like codebase-memory-mcp) for atomic queries.

5. **MCP server vs CLI?** Should pathfinder v2 be an MCP server (like codebase-memory-mcp) rather than a CLI? MCP would integrate natively with Claude Code, Cursor, etc. without shell overhead.
