# Error Patterns & Solutions

## [Error Category 1]

### Error: [ExactErrorName]

**Symptom**:
```
[Exact error message or behavior user sees]
```

**Root Cause**:
[Explanation of why this happens]

**Investigation**:
```bash
# Check [X]
[command]

# Verify [Y]
[command]
```

**Solution**:
```typescript
// [Description of fix]
[code]
```

**Prevention**:
- [How to prevent in future]

---

## [Error Category 2]

### Error: [ExactErrorName]

**Symptom**:
```
[Error message]
```

**Root Cause**:
[Explanation]

**Investigation**:
```bash
[commands]
```

**Solution**:
[Fix description and code]

---

## Quick Diagnosis Table

| Error Contains | Category | First Check | Common Fix |
|----------------|----------|-------------|------------|
| `[keyword1]` | [Category] | [What to check] | [Common solution] |
| `[keyword2]` | [Category] | [What to check] | [Common solution] |
| `[keyword3]` | [Category] | [What to check] | [Common solution] |

## Error Logging

### Where Logs Live
- **API logs**: `logs/api.log` or console in dev
- **Database logs**: [location]
- **External service logs**: [location/dashboard]

### Useful Log Queries
```bash
# Find errors in last hour
grep -i "error" logs/api.log | tail -100

# Find specific error type
grep "[ErrorName]" logs/api.log

# Find errors for specific user
grep "[user_id]" logs/api.log | grep -i "error"
```

## Error Handling Conventions

### API Routes
```typescript
export async function POST(req: Request) {
  try {
    // ... logic
  } catch (error) {
    if (error instanceof ValidationError) {
      return Response.json({ error: error.message }, { status: 400 });
    }
    if (error instanceof AuthError) {
      return Response.json({ error: 'Unauthorized' }, { status: 401 });
    }
    // Log unexpected errors
    console.error('Unexpected error:', error);
    return Response.json({ error: 'Internal error' }, { status: 500 });
  }
}
```

### Custom Error Classes
| Error Class | HTTP Status | When Used |
|-------------|-------------|-----------|
| `ValidationError` | 400 | Invalid input |
| `AuthError` | 401 | Authentication failed |
| `ForbiddenError` | 403 | Permission denied |
| `NotFoundError` | 404 | Resource not found |
| `ConflictError` | 409 | State conflict |
