# Debugging Playbooks

## Playbook: [Issue Type 1]

### When to Use
- User reports [symptom]
- Logs show [pattern]
- [Other trigger conditions]

### Prerequisites
- Access to [systems/logs]
- [Tools/permissions needed]

### Step-by-Step

#### Step 1: Gather Context
```bash
# Get recent errors
[command]

# Check system state
[command]
```

**What to look for**: [Key indicators]

#### Step 2: Reproduce Locally
```bash
# Set up local environment
[command]

# Trigger the issue
[command or steps]
```

**Expected behavior**: [What you should see]

#### Step 3: Identify Root Cause

| If You See | Likely Cause | Go To |
|------------|--------------|-------|
| [Indicator A] | [Cause A] | Step 4a |
| [Indicator B] | [Cause B] | Step 4b |
| [Indicator C] | [Cause C] | Step 4c |

#### Step 4a: Fix for [Cause A]
```typescript
// [Fix description]
[code]
```

#### Step 4b: Fix for [Cause B]
```typescript
// [Fix description]
[code]
```

#### Step 5: Verify Fix
```bash
# Run specific test
[command]

# Manual verification
[steps]
```

### Common Fixes Summary
| Cause | Fix |
|-------|-----|
| [Cause A] | [One-line fix description] |
| [Cause B] | [One-line fix description] |

---

## Playbook: [Issue Type 2]

### When to Use
- [Conditions]

### Step-by-Step

#### Step 1: [Title]
[Instructions]

#### Step 2: [Title]
[Instructions]

[Continue pattern...]

---

## Playbook: [Issue Type 3]

[Same structure]

---

## Quick Debugging Commands

### System Health
```bash
# Check all services
./scripts/check_health.py

# Check specific service
curl http://localhost:3000/api/health
```

### Database
```bash
# Check connection
npm run db:check

# Query recent records
npm run db:query "SELECT * FROM [table] ORDER BY created_at DESC LIMIT 10"

# Check for locks
npm run db:query "SELECT * FROM pg_locks WHERE NOT granted"
```

### Logs
```bash
# Tail API logs
tail -f logs/api.log

# Search for errors
grep -i "error\|exception\|fail" logs/api.log | tail -50

# Filter by request ID
grep "[request_id]" logs/api.log
```

### External Services
```bash
# Check [Service 1] status
curl https://status.[service1].com/api/v1/status

# Test [Service 2] connection
./scripts/test_[service2].sh
```

## Escalation Path

1. **Self-service**: Follow playbooks above
2. **Team help**: Post in #[channel] with:
   - Error message
   - Steps to reproduce
   - What you've tried
3. **On-call**: Page via [system] for:
   - Production outage
   - Data integrity issues
   - Security incidents
