# KB v3 — Corrections Log (Leakage-Safe)

Purpose: capture reusable failure patterns and fixes without storing benchmark answer keys.

Policy:
- Do not store exact benchmark questions.
- Do not store expected outputs, winner identities, forbidden-value lists, or ground-truth numbers.
- Keep entries procedural and dataset-agnostic where possible.

Format:
- Failure pattern
- Root cause
- Correct approach
- Verification note

---

## Entry 001 — Cross-DB Key Normalization

Failure pattern:
- Cross-database joins return zero rows even though related entities exist.

Root cause:
- Equivalent IDs use different string prefixes across systems.

Correct approach:
- Normalize both IDs to a canonical key before joining (for example, extract numeric suffix).
- Validate join cardinality after normalization.

Verification note:
- Add a sanity check query that confirms at least one joined row before final aggregation.

---

## Entry 002 — Mixed Datetime Formats

Failure pattern:
- Time-filtered counts/aggregates are unexpectedly low.

Root cause:
- Single-format datetime parsing drops rows with alternative formats.

Correct approach:
- Use `COALESCE` over multiple `TRY_STRPTIME` patterns.
- For year-only filters, use regex extraction as fallback.

Verification note:
- Compare parsed row count vs total non-null date rows.

---

## Entry 003 — Unstructured Location Fields

Failure pattern:
- City/state filters produce empty or partial results.

Root cause:
- Location is embedded in free text rather than structured columns.

Correct approach:
- Parse location with regex/text functions before filtering.
- Add a fallback parser for alternative phrasing.

Verification note:
- Spot-check parsed state/city values on a random sample.

---

## Entry 004 — String-Typed Numeric/Boolean Fields

Failure pattern:
- Numeric comparisons or boolean logic behave incorrectly.

Root cause:
- Source values are stored as strings.

Correct approach:
- Cast numeric strings before arithmetic.
- Normalize boolean-like values (`"1"`, `"0"`, `"true"`, `"false"`) before filtering.

Verification note:
- Assert conversion success rate and log cast failures.

---

## Entry 005 — Serialized Nested Attributes

Failure pattern:
- Attribute-based filters miss valid entities.

Root cause:
- Nested structures are serialized strings or mixed types.

Correct approach:
- Parse only the serialized nested field when needed.
- Do not parse already-materialized dictionaries.
- Use tolerant matching for value variants.

Verification note:
- Count entities matching each accepted variant.

---

## Entry 006 — Avoid Average-of-Averages

Failure pattern:
- Final averages are biased high/low.

Root cause:
- Averaging per-group averages instead of raw observations.

Correct approach:
- Aggregate directly over row-level measurements whenever the metric requires equal weight per row.

Verification note:
- Compare row-level average with grouped-average result and reject inconsistent method.

---

## Entry 007 — Output Formatting Compatibility

Failure pattern:
- Semantically correct answer fails validation.

Root cause:
- Output includes extra formatting/text that breaks parser assumptions.

Correct approach:
- Return compact plain text.
- Keep paired values adjacent (for example, code and country/value) with minimal separators.

Verification note:
- Run a local formatting check before returning final output.

---

## Entry 008 — Single-Winner Query Discipline

Failure pattern:
- Correct winner is present but response still fails.

Root cause:
- Response includes extra alternatives, rankings, or commentary.

Correct approach:
- For single-winner prompts, return only the winning entity.
- Omit runner-up context unless explicitly requested.

Verification note:
- Enforce response-shape rule in post-processing.

---

## Entry 009 — Top-N Aggregation Completeness

Failure pattern:
- Top categories/entities are incomplete or misordered.

Root cause:
- Aggregation was performed over truncated intermediate subsets.

Correct approach:
- Aggregate over full eligible population before ranking.
- Apply top-N only at the final ranking stage.

Verification note:
- Compare top-N from full run vs sampled/truncated run.

---

## Template

Failure pattern:
- 

Root cause:
- 

Correct approach:
- 

Verification note:
- 
