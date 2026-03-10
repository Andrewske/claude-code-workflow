# System Architecture

## Component Overview

### [Frontend Layer]
- **Framework**: [e.g., Next.js 14 (App Router)]
- **State Management**: [e.g., Zustand, Redux]
- **Key directories**:
  - `src/app/` - Pages and routes
  - `src/components/` - Reusable components
  - `src/hooks/` - Custom React hooks

### [API Layer]
- **Location**: `src/app/api/`
- **Authentication**: [Auth method]
- **Key routes**:
  - `POST /api/[resource]` - [Purpose]
  - `GET /api/[resource]/[id]` - [Purpose]
  - `PUT /api/[resource]/[id]` - [Purpose]

### [Database Layer]
- **Technology**: [e.g., PostgreSQL, MongoDB]
- **ORM**: [e.g., Prisma, Drizzle]
- **Schema location**: [e.g., `prisma/schema.prisma`]

### [External Services]
| Service | Purpose | Client Location |
|---------|---------|-----------------|
| [Service 1] | [Purpose] | `src/lib/[service].ts` |
| [Service 2] | [Purpose] | `src/lib/[service].ts` |

## Component Relationships

```
[Component A] ──uses──▶ [Component B]
      │                      │
      │                      ▼
      │               [Component C]
      │                      │
      ▼                      ▼
[Component D] ◀──shares──▶ [Database]
```

## Data Storage

### Primary Database
- **Tables**: [List key tables]
- **Key relationships**: [Describe]

### Caching Layer
- **Technology**: [Redis/in-memory/etc.]
- **Cache keys**: [Pattern description]
- **TTL**: [Default expiration]

### File Storage
- **Technology**: [S3/R2/local]
- **Bucket structure**: [Description]
- **Access patterns**: [Public/signed URLs]

## Security Model

### Authentication
- [How auth works]
- [Session/token handling]

### Authorization
- [Permission model]
- [Role-based access]

## Configuration

### Environment Variables
| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | Database connection string |
| `[VAR_NAME]` | [Yes/No] | [Description] |

### Feature Flags
| Flag | Default | Description |
|------|---------|-------------|
| `[FLAG_NAME]` | [value] | [Description] |
