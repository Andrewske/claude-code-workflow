# Data Flows

## [Feature 1] Flow

### User Journey
1. User [action]
2. Frontend [behavior]
3. API [processing]
4. [Service/Database] [operation]
5. Response [returned]

### Code Path
```
[Component] (src/components/X.tsx)
    │ [trigger]
    ▼
[Hook/Action] (src/hooks/useX.ts)
    │ [call]
    ▼
[API Route] (src/app/api/x/route.ts)
    │ [processing]
    ▼
[Service] (src/lib/xService.ts)
    │ [operation]
    ▼
[Database] (Table X)
```

### Key Files
| File | Purpose |
|------|---------|
| `src/components/[X].tsx` | UI trigger |
| `src/app/api/[x]/route.ts` | Request handler |
| `src/lib/[x]Service.ts` | Business logic |

### Data Transformations
| Stage | Input | Output |
|-------|-------|--------|
| [Stage 1] | [Input type] | [Output type] |
| [Stage 2] | [Input type] | [Output type] |

---

## [Feature 2] Flow

### User Journey
1. [Step 1]
2. [Step 2]
3. [Step 3]

### Code Path
```
[Diagram]
```

### Key Files
| File | Purpose |
|------|---------|
| [file] | [purpose] |

---

## [Feature 3] Flow

[Same structure]

---

## Cross-Feature Interactions

### [Feature A] ↔ [Feature B]
- [How they interact]
- [Shared data/state]
- [Sequence of operations]

### Common Patterns

#### Database Transaction Pattern
```typescript
await prisma.$transaction(async (tx) => {
  // All operations in single transaction
  await tx.[model].create({ ... });
  await tx.[model].update({ ... });
});
```

#### External Service Call Pattern
```typescript
try {
  const result = await externalService.call(params);
  // Process result
} catch (error) {
  // Handle specific error types
  if (error instanceof TimeoutError) {
    // Retry logic
  }
  throw error;
}
```
