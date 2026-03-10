---
name: querying-[domain]
description: "Query [system/database] for [domain] data including [data types]. Includes schemas, common query patterns, and filtering rules. Use when analyzing [domain] data, writing queries, generating reports, or answering questions about [metrics/entities]. Triggers on '[system name]', '[key terms]', '[metric names]'."
---

# [Domain] Data Access

## Quick Start

Basic query:
```sql
SELECT * FROM [main_table] LIMIT 10
```

## Available Data

| Domain | Tables | Reference |
|--------|--------|-----------|
| [Domain 1] | [tables] | [reference/domain1.md](reference/domain1.md) |
| [Domain 2] | [tables] | [reference/domain2.md](reference/domain2.md) |
| [Domain 3] | [tables] | [reference/domain3.md](reference/domain3.md) |

## Standard Filters

**ALWAYS apply these filters unless explicitly told otherwise:**

```sql
-- Exclude test data
WHERE account_type != 'test'
  AND email NOT LIKE '%@test.%'

-- Use UTC timestamps
WHERE created_at >= TIMESTAMP('2024-01-01', 'UTC')
```

## Common Queries

### [Query Type 1]
```sql
SELECT 
    [columns]
FROM [table]
WHERE [conditions]
GROUP BY [grouping]
```

### [Query Type 2]
```sql
SELECT 
    [columns]
FROM [table]
WHERE [conditions]
ORDER BY [ordering]
```

## Quick Search

```bash
# Find specific metrics
grep -i "[metric]" reference/[domain].md

# Find table schema
grep -A 20 "## [TableName]" reference/schemas.md
```

## Key Metrics Glossary

| Metric | Definition | Calculation |
|--------|------------|-------------|
| [Metric 1] | [Definition] | [Formula/source] |
| [Metric 2] | [Definition] | [Formula/source] |
| [Metric 3] | [Definition] | [Formula/source] |

## Access & Permissions

- **Read access**: [who has it]
- **Write access**: [who has it]
- **Connection string**: Set via `[ENV_VAR]` environment variable
