---
description: Fix all TypeScript typing issues with strict typing principles
argument-hint: [file-path]
allowed-tools: Read, Edit, MultiEdit, Grep, Glob, Bash(tsc:*)
---

# TypeScript Strict Typing Fix Prompt

You are a TypeScript expert tasked with fixing all typing issues in the provided code. Apply strict typing principles systematically.

## Required Actions

### 1. Eliminate Loose Typing
- Replace ALL `any` types with specific, strict types
- Replace ALL `unknown` types with proper type guards or specific types
- Remove ALL non-null assertions (!) - handle null/undefined properly
- Add explicit return types to ALL functions

### 2. Fix TypeScript Errors
- Resolve all red squiggly lines/compiler errors
- Ensure code passes with `strict: true` in tsconfig
- Fix type mismatches and implicit any errors
- Handle all possible null/undefined cases

### 3. Organize Type Definitions
- Group related types together at the top of files
- Use `interface` for object shapes that might be extended
- Use `type` for unions, intersections, and aliases
- Use `enum` or const assertions for fixed sets of values
- Extract shared types to dedicated type files when used across multiple files

### 4. Remove Duplicates
- Identify and consolidate duplicate type definitions
- Create single source of truth for each type
- Use type imports where types are needed

### 5. Database Types (Prisma)
- Import generated Prisma types from '@prisma/client'
- Use Prisma's generated types for all database entities
- Example: `import { User, Post, Prisma } from '@prisma/client'`
- For input types: use `Prisma.UserCreateInput`, `Prisma.UserUpdateInput`, etc.
- For where clauses: use `Prisma.UserWhereInput`, `Prisma.UserWhereUniqueInput`

### 6. Complete Typing Coverage
- Every variable declaration must have a type (inferred or explicit)
- Every function parameter must be typed
- Every function must have an explicit return type
- Every callback and arrow function must be fully typed
- Generic types must have constraints where applicable

## Examples of Fixes

BEFORE:
```typescript
const processData = (data: any) => {
  return data.items!.map((item: any) => item.name)
}
```

AFTER:
```typescript
interface DataItem {
  name: string;
  // other properties
}

interface ProcessDataInput {
  items?: DataItem[];
}

const processData = (data: ProcessDataInput): string[] => {
  if (!data.items) {
    return [];
  }
  return data.items.map((item) => item.name);
}
```

## Validation Checklist
After making changes, verify:
- [ ] No `any` types remain
- [ ] No `unknown` types remain without type guards
- [ ] No non-null assertions (!)
- [ ] All functions have explicit return types
- [ ] No TypeScript errors with strict mode
- [ ] Prisma types used for all DB operations
- [ ] No duplicate type definitions

Proceed systematically through the code, fixing each issue completely before moving to the next.