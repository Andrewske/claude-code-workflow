---
name: understanding-[project-name]
description: "Deep knowledge of [Project Name] architecture, data flows, debugging patterns, and codebase navigation. Covers [tech stack summary]. Use when investigating bugs, understanding features, tracing issues, debugging errors, or answering architecture questions. Triggers on 'how does X work', 'why is Y broken', 'trace the flow', 'debug this', '[project name]', '[key component names]'."
---

# [Project Name] Knowledge Base

## Architecture Overview

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  [Layer 1]  │────▶│  [Layer 2]  │────▶│  [Layer 3]  │
│  [Tech]     │     │  [Tech]     │     │  [Tech]     │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  [Layer 4]  │◀───▶│  [Layer 5]  │     │  [Layer 6]  │
│  [Tech]     │     │  [Tech]     │     │  [Tech]     │
└─────────────┘     └─────────────┘     └─────────────┘
```

## Entry Points

| User Action | Entry File | Details |
|-------------|------------|---------|
| [Action 1] | `path/to/file.tsx` | [reference/data-flows.md#action1](reference/data-flows.md#action1) |
| [Action 2] | `path/to/file.ts` | [reference/data-flows.md#action2](reference/data-flows.md#action2) |
| [Action 3] | `path/to/route.ts` | [reference/data-flows.md#action3](reference/data-flows.md#action3) |

## Quick Diagnostics

### Find Related Files
```bash
grep -rl "[keyword]" --include="*.ts" --include="*.tsx" src/
```

### Run Health Check
```bash
./scripts/check_health.py
```

### Trace a Flow
```bash
./scripts/trace_flow.py [feature-name]
```

## Common Errors

| Symptom | Likely Cause | Playbook |
|---------|--------------|----------|
| [Error 1] | [Cause] | [reference/error-patterns.md#error1](reference/error-patterns.md#error1) |
| [Error 2] | [Cause] | [reference/error-patterns.md#error2](reference/error-patterns.md#error2) |
| [Error 3] | [Cause] | [reference/error-patterns.md#error3](reference/error-patterns.md#error3) |

## Deep Dives

- **Architecture**: [reference/architecture.md](reference/architecture.md)
- **Data Flows**: [reference/data-flows.md](reference/data-flows.md)
- **Error Patterns**: [reference/error-patterns.md](reference/error-patterns.md)
- **Debug Playbooks**: [reference/debugging-playbooks.md](reference/debugging-playbooks.md)

## Essential Commands

| Command | Purpose |
|---------|---------|
| `npm run dev` | Start development server |
| `npm run test` | Run test suite |
| `npm run build` | Production build |
| `npm run lint` | Check code quality |
| `npm run db:push` | Push database schema |

## Key Environment Variables

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | Database connection |
| `[API_KEY]` | External service auth |
| `[OTHER_VAR]` | [Purpose] |

## File Structure

```
src/
├── app/           # Pages and API routes
├── components/    # React components
├── lib/           # Shared utilities
├── hooks/         # Custom React hooks
├── services/      # Business logic
└── types/         # TypeScript types
```
