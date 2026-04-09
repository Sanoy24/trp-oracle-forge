# Claude Code Memory and Context Architecture

## Three-Layer Memory System

Claude Code persists knowledge across sessions using a file-based memory hierarchy:

**Layer 1 — Project Memory (`CLAUDE.md`)**
A markdown file at the project root, loaded automatically at startup. Contains project-specific conventions, architecture notes, and rules. Subdirectories can have their own `CLAUDE.md` files that layer on top.

**Layer 2 — User Memory (`~/.claude/CLAUDE.md`)**
A user-level file loaded across all projects. Stores personal preferences and cross-project patterns.

### Layer 3 — Extracted and Session Memory

- `extractMemories` — automatically extracts reusable facts from conversations and persists them.
- `SessionMemory` — maintains state within a single working session.
- `teamMemorySync` — synchronizes shared knowledge across team members.

## autoDream Consolidation

The `DreamTask` (`src/tasks/DreamTask/`) runs as a background process. It consolidates patterns from recent interactions into structured memory — analogous to how sleep consolidates learning. This is how the system converts ephemeral session observations into durable knowledge without user intervention.

## Context Assembly and Compression

At query time, `src/context.ts` assembles the full context: OS environment, shell state, git status, user identity, plus all memory layers. When the conversation approaches context window limits, `src/services/compact/` compresses prior messages so the session can continue without losing critical information. The `/compact` command triggers this manually.

## Tool Scoping Philosophy

Every capability is a self-contained tool (`src/tools/<ToolName>/`) with four components: input schema (Zod-validated), permission model, execution logic, and UI rendering. Tools declare concurrency safety via `isConcurrencySafe()` so safe tools run in parallel. Tools are grouped into presets for different contexts (read-only review vs full development). Capabilities can be added or restricted without touching the core query engine.

## MCP as the Extension Interface

The Model Context Protocol (`src/services/mcp/`) lets Claude Code consume external tools and data sources through a standard interface. A single `tools.yaml` defines all connected servers. MCP tools are discovered dynamically and invoked identically to built-in tools. Claude Code can also run as an MCP server, exposing its tools to other agents.

## Key Design Insight for Data Agents

The architecture separates what the agent knows (memory layers) from what the agent can do (tools) from how the agent decides (query engine). Context is assembled before the LLM sees anything. This means a data agent can inject domain knowledge, schema descriptions, and correction history as context layers — making the agent smarter without changing the model or the tools.
