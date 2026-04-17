# StockIndex Domain Knowledge (Leakage-Safe)

## Scope

This file contains methodology and schema interpretation guidance only.
Do not store or use query-specific expected answers, ranked winner lists, forbidden symbol lists, or ground-truth numeric values.

---

## Dataset Overview

Two databases are used in this dataset:

| Database | Type | Logical Name | Table | Key Fields |
|----------|------|--------------|-------|------------|
| indexInfo_query.db | SQLite | indexinfo_database | index_info | Exchange (text), Currency (text) |
| indextrade_query.db | DuckDB | indextrade_database | index_trade | Index (text), Date (text), Open, High, Low, Close, Adj Close, CloseUSD (numeric) |

There is no direct relational foreign key between the two tables. Region/country attributes are often inferred from exchange metadata.

---

## Region/Exchange Resolution

Resolve symbol geography from data at runtime instead of relying on pre-listed winners.

Recommended pattern:

```sql
SELECT Exchange, Currency
FROM index_info;
```

Then build region grouping logic from exchange names in your query plan.
Do not hardcode final winners or ranked outputs.

---

## Calculation Definitions

### Intraday Volatility

```sql
SELECT "Index",
  AVG(("High" - "Low") / NULLIF("Open", 0)) AS avg_volatility
FROM index_trade
WHERE <date filter>
GROUP BY "Index"
ORDER BY avg_volatility DESC
```

Use the winner row from query output. Do not assume the winner in advance.

### Up/Down Day Definition

Use intraday movement:

```sql
SUM(CASE WHEN "Close" > "Open" THEN 1 ELSE 0 END) AS up_days,
SUM(CASE WHEN "Close" < "Open" THEN 1 ELSE 0 END) AS down_days
```

Avoid day-over-day substitutes (`Close > previous Close`) unless the question explicitly asks for day-over-day logic.

### Periodic Investment Style Queries

When a prompt asks for regular/monthly investments, avoid naive first-to-last buy-and-hold unless explicitly requested.
Use month-bucketed return aggregation when the question describes periodic contributions.

```sql
WITH parsed AS (
  SELECT "Index",
    COALESCE(
      TRY_STRPTIME("Date", '%Y-%m-%d %H:%M:%S'),
      TRY_STRPTIME("Date", '%B %d, %Y at %I:%M %p'),
      TRY_STRPTIME("Date", '%d %b %Y, %H:%M'),
      TRY_STRPTIME("Date", '%d %B %Y, %H:%M'),
      TRY_STRPTIME("Date", '%B %d, %Y at %H:%M'),
      TRY_STRPTIME("Date", '%m/%d/%Y %H:%M:%S')
    ) AS dt,
    "CloseUSD"
  FROM index_trade
),
monthly AS (
  SELECT "Index", DATE_TRUNC('month', dt) AS month,
    FIRST("CloseUSD" ORDER BY dt) AS open_price,
    LAST("CloseUSD" ORDER BY dt)  AS close_price
  FROM parsed
  WHERE dt IS NOT NULL AND "CloseUSD" IS NOT NULL AND "CloseUSD" > 0
  GROUP BY "Index", DATE_TRUNC('month', dt)
)
SELECT "Index", SUM(close_price / open_price - 1) * 100 AS total_return
FROM monthly
GROUP BY "Index"
ORDER BY total_return DESC;
```

---

## Date Parsing

The `Date` field can contain mixed formats in the same column.
Always use multi-pattern `COALESCE(TRY_STRPTIME(...))` and filter out null parse results.

---

## Output Policy

- Compute answers from tool/query outputs at runtime.
- Do not rely on memorized benchmark outputs.
- For single-winner questions, return only the winner.
- For paired outputs (symbol + country/value), keep values adjacent in compact plain text.
