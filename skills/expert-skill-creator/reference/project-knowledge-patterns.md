# Project Knowledge Skill Patterns

Specific patterns for creating skills that document project architecture, debugging workflows, and codebase navigation.

## Why Project Skills Are High Value

Project knowledge is exactly what Claude **doesn't** have:
- Your specific file structure
- Your error patterns and fixes
- Your debugging workflows
- Your team's conventions

A well-crafted project skill turns Claude into a team member who knows your codebase.

## Core Components

Every project knowledge skill should cover:

| Component | Purpose | Example |
|-----------|---------|---------|
| Architecture overview | Mental map | ASCII diagram of services |
| Entry points | Where code starts | User action → file mapping |
| Data flows | How data moves | Request → response path |
| Error patterns | Known issues | Error message → root cause |
| Debug playbooks | How to investigate | Step-by-step guides |
| Key commands | Essential operations | Dev, test, deploy |

## Architecture Documentation Patterns

### ASCII Diagrams
```markdown
## System Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Next.js   │────▶│   API       │────▶│  External   │
│   Frontend  │     │   Routes    │     │  Services   │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Zustand   │◀───▶│  PostgreSQL │     │   S3/R2     │
│   State     │     │  (Prisma)   │     │  Storage    │
└─────────────┘     └─────────────┘     └─────────────┘
```
```

ASCII works perfectly in markdown and renders clearly.

### Component Table
```markdown
## Components

| Layer | Technology | Location | Purpose |
|-------|------------|----------|---------|
| Frontend | Next.js 14 | `src/app/` | UI, routing |
| State | Zustand | `src/store/` | Client state |
| API | Route handlers | `src/app/api/` | Backend logic |
| Database | PostgreSQL | `prisma/schema.prisma` | Persistence |
| Storage | Cloudflare R2 | `src/lib/storage.ts` | File uploads |
| Auth | NextAuth | `src/lib/auth.ts` | Authentication |
```

### Service Boundaries
```markdown
## Service Boundaries

### Frontend (Next.js)
- **Owns**: UI rendering, client state, routing
- **Talks to**: API routes only
- **Never**: Direct database access

### API Layer
- **Owns**: Business logic, validation, auth checks
- **Talks to**: Database, external services
- **Never**: UI concerns

### Database
- **Owns**: Data persistence, relationships
- **Talks to**: Only API layer (via Prisma)
```

## Entry Point Mapping Patterns

### User Action Table
```markdown
## Entry Points

| User Action | Entry File | Flow |
|-------------|------------|------|
| Login | `src/app/login/page.tsx` | [auth flow](#auth-flow) |
| Upload image | `src/app/upload/page.tsx` | [upload flow](#upload-flow) |
| Generate image | `src/components/Generator.tsx` | [generation flow](#generation-flow) |
| Purchase credits | `src/app/pricing/page.tsx` | [payment flow](#payment-flow) |
```

### Code Path Trace
```markdown
## Auth Flow

```
[LoginPage] (src/app/login/page.tsx)
    │ onClick → signIn()
    ▼
[NextAuth] (src/lib/auth.ts)
    │ credentials provider
    ▼
[API Route] (src/app/api/auth/[...nextauth]/route.ts)
    │ verify credentials
    ▼
[Database] (prisma/schema.prisma - User table)
    │ return user
    ▼
[Session] → JWT token created
```
```

## Data Flow Documentation Patterns

### Flow Diagram
```markdown
## Image Generation Flow

```
1. User clicks "Generate"
   └─▶ GenerateButton.tsx
   
2. Client sends request
   └─▶ POST /api/generate
   
3. API validates & deducts credits
   └─▶ creditService.deduct()
   └─▶ Prisma transaction
   
4. API calls external service
   └─▶ imagenClient.generate()
   └─▶ Google Imagen API
   
5. Image stored
   └─▶ storageService.upload()
   └─▶ Cloudflare R2
   
6. Response returned
   └─▶ { imageUrl, creditsRemaining }
```
```

### Data Transformation Points
```markdown
## Data Transformations

| Stage | Input | Output | Location |
|-------|-------|--------|----------|
| Upload | File blob | R2 URL | `src/lib/storage.ts` |
| Generate request | Form data | API payload | `src/lib/api.ts` |
| Imagen response | Base64 | PNG buffer | `src/lib/imagen.ts` |
| Credit deduction | User ID | Transaction | `src/services/credits.ts` |
```

## Error Pattern Documentation

### Error Catalog
```markdown
## Common Errors

### CreditError: Insufficient credits
**Symptom**: User sees "Not enough credits" toast
**Root cause**: Credit check failed before generation
**Investigation**:
```bash
# Check user's credit balance
npm run db:query "SELECT credits FROM users WHERE id = '<user_id>'"
```
**Fix**: User needs to purchase more credits

---

### TimeoutError: Imagen API timeout
**Symptom**: Generation spinner indefinitely, then error
**Root cause**: Imagen API took >30s to respond
**Investigation**:
```bash
# Check API logs
grep "TimeoutError" logs/api.log | tail -20
```
**Fix**: Retry usually works; if persistent, check Imagen status page

---

### UploadError: R2 multipart failure
**Symptom**: Upload stuck at 99%
**Root cause**: R2 multipart upload didn't complete
**Investigation**:
```bash
# Check incomplete uploads
npm run storage:list-incomplete
```
**Fix**: Abort incomplete upload, retry
```

### Quick Diagnosis Table
```markdown
## Quick Diagnosis

| Error Contains | Likely Cause | First Check |
|----------------|--------------|-------------|
| `CREDIT` | Credit system | User balance |
| `AUTH` | Authentication | Session/token |
| `TIMEOUT` | External service | Service status |
| `PRISMA` | Database | Connection/schema |
| `R2` or `S3` | Storage | Bucket permissions |
| `IMAGEN` | Generation API | API key/quota |
```

## Debug Playbook Patterns

### Step-by-Step Playbook
```markdown
## Playbook: Generation Not Working

### Step 1: Check Error Type
```bash
grep -i "error" logs/api.log | tail -50
```

Identify error category:
- Credit error → [Credit Playbook](#credit-issues)
- Timeout → [Timeout Playbook](#timeout-issues)  
- Auth error → [Auth Playbook](#auth-issues)

### Step 2: Reproduce Locally
```bash
# Start dev server with debug logging
DEBUG=* npm run dev
```

Trigger generation, watch console for:
- API route hit
- Credit check
- Imagen call
- Storage upload

### Step 3: Check External Services
```bash
# Imagen API status
curl https://status.cloud.google.com/

# R2 connectivity
npm run storage:health
```

### Step 4: Database State
```bash
# Check user's recent generations
npm run db:query "
  SELECT * FROM generations 
  WHERE user_id = '<id>' 
  ORDER BY created_at DESC 
  LIMIT 5
"
```

### Step 5: If Still Stuck
- Check #engineering Slack for known issues
- Search GitHub issues
- Escalate to on-call
```

### Diagnostic Script Pattern
```markdown
## Automated Diagnostics

Run comprehensive health check:
```bash
./scripts/diagnose.sh <user_id>
```

Output includes:
- User credit balance
- Recent generation attempts
- Error log excerpts
- Service connectivity status
```

## Search Pattern Documentation

For large codebases, include grep patterns:

```markdown
## Finding Things

### By Feature
```bash
# Find generation-related code
grep -rl "generation\|imagen" --include="*.ts" src/

# Find credit system code
grep -rl "credit\|balance" --include="*.ts" src/
```

### By Error
```bash
# Find where specific error is thrown
grep -rn "CreditError" --include="*.ts" src/

# Find error handling
grep -rn "catch.*Error" --include="*.ts" src/
```

### By Pattern
```bash
# Find API routes
find src/app/api -name "route.ts"

# Find React hooks
grep -rl "^export.*use[A-Z]" --include="*.ts" src/hooks/
```
```

## Essential Commands Section

```markdown
## Commands

### Development
| Command | Purpose |
|---------|---------|
| `npm run dev` | Start dev server (port 3000) |
| `npm run build` | Production build |
| `npm run lint` | Run ESLint |
| `npm run typecheck` | TypeScript check |

### Database
| Command | Purpose |
|---------|---------|
| `npm run db:push` | Push schema changes |
| `npm run db:studio` | Open Prisma Studio |
| `npm run db:seed` | Seed test data |
| `npm run db:query "<sql>"` | Run raw query |

### Testing
| Command | Purpose |
|---------|---------|
| `npm run test` | Run all tests |
| `npm run test:watch` | Watch mode |
| `npm run test -- --grep "credit"` | Run specific tests |

### Debugging
| Command | Purpose |
|---------|---------|
| `./scripts/diagnose.sh <user_id>` | Full diagnostic |
| `./scripts/trace_request.sh <request_id>` | Trace request flow |
| `tail -f logs/api.log` | Watch API logs |
```

## File Organization

Recommended structure for project knowledge skill:

```
project-knowledge/
├── SKILL.md                      # Overview, navigation, quick reference
├── reference/
│   ├── architecture.md           # System design, components
│   ├── data-flows.md             # User flows, data paths
│   ├── error-patterns.md         # Error catalog, diagnosis
│   ├── debugging-playbooks.md    # Step-by-step investigations
│   └── api-reference.md          # Internal API documentation
└── scripts/
    ├── diagnose.sh               # Comprehensive health check
    ├── find_related.sh           # Find related files
    └── trace_flow.py             # Trace data through system
```

Keep SKILL.md as navigation hub, details in reference files.
