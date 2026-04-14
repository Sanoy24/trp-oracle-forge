# Operations Report — Sprint 1
**Project:** Oracle Forge — Data Analytics Agent
**Sprint:** 1 of 2 (Week 8, Days 3–5)
**Date recorded:** 2026-04-14
**Type:** Post-sprint retrospective — what actually happened vs the plan

---

## 1. What the Plan Said

From `planning/inception_sprint1.md`:

- Dataset scope: Yelp only (MongoDB + DuckDB, already loaded on server)
- DB types: 2 (MongoDB for business/checkin, DuckDB for review/tip/user)
- Agent framework: DAB `common_scaffold` with custom context-layer extensions
- LLM provider: Anthropic Claude via direct API
- Target: A working baseline pass@1 score on 7 Yelp DAB queries
- Self-correction loop: Corrections log captures every failure for Sprint 2 improvement

---

## 2. What Actually Happened

### Infrastructure

| Planned | Delivered |
|---|---|
| 2 DB types (MongoDB + DuckDB) | 4 DB types: MongoDB, DuckDB, PostgreSQL, SQLite all configured and connected |
| Yelp dataset only | All 12 DAB datasets loaded and available in the agent's database routing config |
| Direct Anthropic API (Sonnet/Opus) | OpenRouter API with `anthropic/claude-haiku-4.5` — cheaper model, proxied through OpenRouter rather than direct Anthropic key |

**Note on model:** The plan specified Sonnet as default and Opus for complex queries. What actually ran was `anthropic/claude-haiku-4.5` via OpenRouter — a significantly smaller and cheaper model. All scores in the log were produced by Haiku, not Sonnet.

**Note on datasets:** Although all 12 datasets were loaded and all 4 DB types confirmed working, **only the Yelp dataset was evaluated through the harness**. Cross-dataset queries were not benchmarked in Sprint 1. The infrastructure is ready; the score record is Yelp-only.

### Score Progression (Yelp, 7 queries)

All evaluation runs were on **2026-04-13**. Source: `eval/score_log.json`.

| Run ID | Agent | Passed | Score | Notes |
|---|---|---|---|---|
| 2026-04-13-001 | `dummy` | 0/7 | 0.00% | Baseline — all "No answer" |
| 2026-04-13-002 | `dummy` | 0/7 | 0.00% | Baseline confirmed |
| 2026-04-13-003 | `data_agent` | **3/7** | **42.86%** | First real run: cross-DB join fix applied; queries 1, 2, 6 pass |
| 2026-04-13-004 | `data_agent` | **3/7** | **42.86%** | Queries 1, 3, 6 pass; query 2 timed out (120 s) |
| 2026-04-13-005 | `data_agent` | 2/7 | 28.57% | Regression: query 3 drops (23 vs 35 — `ast.literal_eval` bug reintroduced) |
| 2026-04-13-006 | `data_agent` | 1/7 | 14.29% | OpenRouter weekly token limit hit after query 1 (402 error) |
| 2026-04-13-007 | `data_agent` | 0/7 | 0.00% | Full key exhaustion (403 on every query) |

**First real run:** 0/7 → 3/7 (runs 001–002 → run 003)
**Peak score:** 3/7 = 42.86% (runs 003 and 004)
**Sprint-end score:** 0/7 (key exhaustion — not a regression in logic, a resource failure)

### Per-Query Status at Sprint End

| Query | Question (abbreviated) | Best result | Notes |
|---|---|---|---|
| query1 | Avg rating — Indianapolis businesses | ✅ PASS (runs 003–006) | Reliable |
| query2 | State with most reviews + avg rating | ✅ PASS (run 003); ❌ runs 004–007 | Inconsistent — timeout, then wrong format, then token exhaustion |
| query3 | 2018 businesses with parking | ✅ PASS (run 004); ❌ run 005 | Regression: `ast.literal_eval` applied to wrong object |
| query4 | Category with most credit-card biz + avg | ⚠️ Partial (run 005: category right, avg 3.59 vs 3.63) | Missing 5 of 27 restaurants |
| query5 | State with most WiFi biz + avg rating | ❌ All runs | Avg computed over all states (3.69–3.72) vs PA-only (3.48) |
| query6 | Highest-rated business H1 2016 | ✅ PASS (runs 003–005) | Reliable |
| query7 | Top 5 categories from 2016 users | ❌ All runs | Missing "Breakfast & Brunch" — category tied at position 5, truncated |

---

## 3. Knowledge Built During Sprint 1

### Adversarial Probes Written: 15

See `probes/probes.md` for full probe library. Status at sprint close:

| Status | Count | Probe IDs |
|---|---|---|
| ✅ Fixed and verified PASS | 5 | PROBE-001, 003, 004, 006, 009 |
| ⚠️ Partial (close but not passing) | 3 | PROBE-005, 011, 013 |
| 🔄 Fix documented, pending re-run | 7 | PROBE-002, 007, 008, 010, 012, 014, 015 |

### Corrections Documented in AGENT.md: 5

| Correction | Issue | Status |
|---|---|---|
| CORRECTION 1 | `attributes` already a Python dict — do NOT `ast.literal_eval` the whole dict | In AGENT.md §8 |
| CORRECTION 2 | No `category` field — extract from `description` text with regex | In AGENT.md §8 |
| CORRECTION 3 | WiFi stored as `"u'free'"` — use substring check not equality | In AGENT.md §8 |
| CORRECTION 4 | Category aggregation — sum across ALL reviewed businesses, not just top N by volume | In AGENT.md §8 |
| CORRECTION 5 | Top N categories — always output N+2 to catch ties | In AGENT.md §8 |

### Context Layers Implemented: 3

1. **AGENT.md** (schema + mandatory rules): Loaded at session start. Contains DB schema, join key map, 5 quick-reference rules, correction protocol, 5 known corrections.
2. **kb/domain/** (institutional knowledge): Domain terminology and business-logic context.
3. **kb/corrections/** (learning memory): Corrections log for agent failures. Template live; entries to be backfilled from probes in Sprint 2.

---

## 4. What Changed from the Plan

| Plan assumption | What actually happened | Impact |
|---|---|---|
| Direct Anthropic API (Sonnet/Opus) | OpenRouter with `anthropic/claude-haiku-4.5` — different provider AND smaller model tier than planned; weekly token limit ~22,000 prompt tokens | Two changes from plan: provider switched to OpenRouter AND model downgraded to Haiku. Run 006 hit the weekly limit mid-run; runs 006–007 effectively useless. Sprint 2 must resolve both before benchmarking. |
| Yelp only in Sprint 1 | All 12 datasets loaded, PostgreSQL and SQLite added | Infrastructure ahead of plan; score record behind plan (only Yelp was evaluated) |
| 7 Yelp queries as stated in plan | Actually 7 queries (not 8 as written in the template placeholder) | No change in plan |
| Agent built from scratch | DAB `common_scaffold` used as base | Saved significant time on harness integration |
| Score target: any baseline | Achieved 3/7 (42.86%) peak; fell to 0/7 at sprint close due to token exhaustion | Good signal — agent logic works; token budget is the constraint, not reasoning quality |

---

## 5. Unresolved Going into Sprint 2

1. **OpenRouter weekly token limit** — must be resolved before any benchmark run. Options: raise limit, switch to direct Anthropic API, or use a fresh key.
2. **7 probes pending re-run** — fixes are documented in AGENT.md but could not be validated before key exhaustion.
3. **query5 (WiFi state + avg)** — the 3-step algorithm (CORRECTION 3 in AGENT.md) is the hardest remaining fix; agent has not passed this in any run.
4. **query7 (top 5 categories)** — requires both the N+2 output rule AND correct category aggregation across all 62 reviewed businesses.
5. **kb/corrections log** — template is live but entries have not been backfilled from probe library. Sprint 2 should add at least the 5 core corrections as structured entries.
