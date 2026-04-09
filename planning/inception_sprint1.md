# AI-DLC Inception Document — Sprint 1
**Project:** Oracle Forge — Data Analytics Agent  
**Sprint:** 1 of 2 (Week 8, Days 3-5)  
**Focus:** Infrastructure + Core Agent Build  
**Date drafted:** 2026-04-09  
**Approval status:** PENDING — must be approved at mob session before Construction begins

---

## 1. Press Release

The Oracle Forge team has deployed a working natural language data analytics agent on our shared EC2 server, capable of answering real business questions against the Yelp dataset using PostgreSQL and SQLite. The agent accepts a plain English question, routes it to the correct database, generates and executes a query, and returns a verified answer with a full query trace — in under 30 seconds. It operates with three context layers: schema and metadata knowledge pre-loaded at session start, institutional knowledge injected from our LLM Knowledge Base, and a corrections log that captures every failure so the agent improves across sessions. The evaluation harness runs automatically after each agent change, producing a pass@1 score against a held-out set of Yelp queries so the team knows immediately whether any change made the agent better or worse. This is the foundation layer — two database types, one dataset, basic NL-to-query working — built in five days by a team of five. It is not the finished product. It is the scaffold on which Sprint 2 will build.

---

## 2. Honest FAQ — User

**Q1: What can the agent actually answer at the end of Sprint 1?**  
It can answer natural language questions about the Yelp dataset that involve a single database (PostgreSQL or SQLite). For example: "Which business categories have the highest average review rating?" or "How many users have written more than 10 reviews?" It cannot yet handle questions that require joining data across two different database systems in the same query — that is a Sprint 2 goal.

**Q2: How accurate is it?**  
We do not know yet — that is what the evaluation harness will measure. Our target for Sprint 1 is a working baseline score on Yelp queries, not a high score. Expect failures on queries involving ambiguous business terms, ill-formatted keys, or questions that require domain knowledge we have not yet written into the Knowledge Base. Every failure will be logged and fed back into the corrections log for Sprint 2.

**Q3: Can I ask it questions about other datasets or databases?**  
Not reliably in Sprint 1. The agent's context layers — schema knowledge, domain terms, join key formats — are built specifically around the Yelp dataset. Extending to other DAB datasets (retail, telecom, healthcare) is a Sprint 2 goal once the architecture is validated on Yelp.

---

## 3. Honest FAQ — Technical

**Q1: What is the hardest technical challenge in Sprint 1?**  
Getting the three context layers to actually work together, not just exist. It is straightforward to create a Knowledge Base directory and write an AGENT.md. It is much harder to confirm that the agent is genuinely using the schema knowledge and KB documents when forming queries — rather than ignoring them and falling back on the LLM's pretrained knowledge. Every context layer must have an injection test that proves it changes the agent's behaviour. This is where most of the Sprint 1 time will go.

**Q2: What is most likely to go wrong?**  
MCP Toolbox configuration. The tools.yaml file must define correct connection strings, tool names, and schema introspection calls for PostgreSQL and SQLite. If this is misconfigured, the agent cannot reach the databases and nothing works. A secondary risk is that the Yelp dataset schema in PostgreSQL does not match our KB documentation, causing the agent to generate queries against column names that do not exist. We will validate both on Day 1 before writing any agent code.

**Q3: What are the key external dependencies?**  
Three: (1) Anthropic Claude API access — the agent calls Claude for NL-to-query generation; if API access is unavailable or rate-limited we cannot run the agent. (2) The DAB repository — we need the Yelp dataset loaded via `bash setup/load_postgres.sh`; if the setup scripts fail we need to debug before Construction begins. (3) MCP Toolbox binary — we pin to version 0.30.0; if the download fails or the binary is incompatible with our server we need a fallback plan (direct database drivers per DB type).

---

## 4. Key Decisions

**Decision 1 — LLM provider for agent**  
**Chosen:** Anthropic Claude via API (claude-sonnet-4-6 as default, claude-opus-4-6 for complex multi-step reasoning)  
**Rationale:** The team has confirmed API access, Claude's tool-use and structured output capabilities are well-suited to the query generation and self-correction loop, and the claude-code-source-code leak gives the team direct insight into how Claude handles multi-layer context — making it the most studied option available to us.

**Decision 2 — Agent framework**  
**Chosen:** DAB `common_scaffold` as base with custom extensions for context layers and self-correction  
**Rationale:** The scaffold provides the standard agent interface DAB's evaluation harness expects (`{question, available_databases, schema_info}` → `{answer, query_trace, confidence}`), so we do not spend Sprint 1 writing evaluation glue code; custom extensions handle the three context layers, the corrections log loop, and multi-database routing that the scaffold does not provide out of the box.

**Decision 3 — Starting dataset**  
**Chosen:** Yelp (PostgreSQL + SQLite, included in DAB)  
**Rationale:** The practitioner manual explicitly recommends Yelp as the starting point — it contains multi-source data, nested JSON, missing values, and entity resolution challenges that represent the full DAB problem space in a contained form, allowing us to validate the agent architecture before extending to other datasets.

---

## 5. Definition of Done

Sprint 1 is complete when all of the following are verifiably true. "I think it works" is not evidence. Each item requires a specific observable output.

1. **MCP Toolbox is running and all connections verified:** `curl http://localhost:5000/v1/tools` returns tool definitions for at least PostgreSQL and SQLite. Screenshot saved to `docs/toolbox-verified.png`.

2. **Yelp dataset is loaded and queryable:** Running `python eval/run_query.py --dataset yelp --query 0` in the DAB repository returns a structured result JSON with a non-empty answer field. Output saved to `docs/yelp-query0-raw.json`.

3. **Agent answers Yelp query 0 correctly with query trace:** The agent, called via the standard DAB interface, returns the correct answer to Yelp query 0 within 30 seconds. The response includes a `query_trace` field showing the SQL or query executed. Output saved to `docs/yelp-query0-agent.json`.

4. **All three context layers are loaded and injection-tested:** `AGENT.md` is committed to `agent/` and loads schema context at session start. At least two documents in `kb/architecture/` and one in `kb/domain/` have passed their injection test (test query + expected answer documented in the respective `CHANGELOG.md`).

5. **Evaluation harness produces a baseline score:** Running the harness against the held-out Yelp query set returns a pass@1 score (any number, including 0%). Score and run metadata are committed to `eval/score_log.md` as Run #1.

6. **Agent is running on the shared server and accessible:** Any team member can SSH to the server and run the agent from a fresh terminal session following only the instructions in `README.md`. The Driver demonstrates this live at the Sprint 1 close mob session.

7. **Signal Corps: first post live and Slack log started:** At least one substantive X thread is live (link committed to `signal/engagement_log.md`). Daily Slack posts have been made for at least Days 3–5 of the sprint.

8. **This Inception document is mob-approved:** The full team has read this document together, asked their hardest questions, and given explicit group approval. Approval is recorded below with the date, who approved, and the hardest question asked and its answer.

---

## Mob Approval Record

**Status:** PENDING

| Field | Value |
|-------|-------|
| Approval date | |
| Approved by | |
| Hardest question asked | |
| Answer given | |
| Any items sent back for revision | |

*No Construction work begins until this section is filled in and committed.*
