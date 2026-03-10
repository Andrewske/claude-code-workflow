# [Domain] Data Reference

## Tables

### [table_name]

**Purpose**: [What this table stores]

**Schema**:
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| [column1] | [type] | [Description] |
| [column2] | [type] | [Description] |
| [column3] | [type] | [Description] |
| created_at | TIMESTAMP | Record creation time (UTC) |
| updated_at | TIMESTAMP | Last modification time (UTC) |

**Key relationships**:
- `[column]` → `[other_table].[column]`

**Common filters**:
```sql
-- Active records only
WHERE status = 'active'

-- Recent records
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
```

---

### [another_table]

[Same structure as above]

---

## Common Query Patterns

### [Pattern Name 1]
**Use case**: [When to use this pattern]

```sql
SELECT 
    t1.[columns],
    t2.[columns]
FROM [table1] t1
JOIN [table2] t2 ON t1.[key] = t2.[key]
WHERE [conditions]
GROUP BY [grouping]
ORDER BY [ordering]
```

### [Pattern Name 2]
**Use case**: [When to use this pattern]

```sql
[Query]
```

---

## Data Quality Notes

- [Note about data quality, known issues, etc.]
- [Note about refresh frequency]
- [Note about historical data availability]
