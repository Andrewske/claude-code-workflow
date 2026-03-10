# Update Project Skill

Intelligently update the project knowledge skill based on codebase changes.

## Determine Update Mode

Based on the user's request, determine which mode to use:

**Mode 1: Git-Based Update** (user mentions "git", "commits", "recent changes", or no specific focus)
→ Analyze recent git commits to find what changed and update skill accordingly

**Mode 2: Specific Area Update** (user mentions specific area like "auth", "database", "api")
→ Focus on that specific area, compare skill docs to actual code

**Mode 3: Full Audit** (user says "full", "audit", "everything", "comprehensive")
→ Review entire skill against codebase for staleness

**Mode 4: Error Pattern Capture** (user mentions "error", "bug", "issue we just hit")
→ Add a new error pattern to error-patterns.md

---

## Mode 1: Git-Based Update

Run this to see recent changes:

```bash
# Get summary of changes in last N commits (default 10)
git log --oneline -10

# Get files changed in last 10 commits
git diff --name-only HEAD~10..HEAD

# Get detailed diff for architecture-relevant files
git diff HEAD~10..HEAD --stat
```

Then:

1. **Identify impactful changes:**
   - New files/directories (new features?)
   - Deleted files (removed features?)
   - Modified API routes (flow changes?)
   - Schema changes (data model updates?)
   - New error types or error handling

2. **Cross-reference with skill:**
   - Read current `.claude/skills/project-knowledge/SKILL.md`
   - Read relevant reference files
   - Identify mismatches

3. **Propose specific patches:**
   - Don't rewrite entire files
   - Show exact additions/changes needed
   - Explain why each change matters

---

## Mode 2: Specific Area Update

1. **Identify relevant files:**
```bash
# Find files related to the area
grep -rl "[AREA]" --include="*.ts" --include="*.tsx" src/
find src -name "*[area]*" -type f
```

2. **Read current skill documentation** for that area

3. **Compare actual code vs documented behavior:**
   - Are the entry points still correct?
   - Are the data flows still accurate?
   - Are there new error cases?

4. **Propose targeted updates** to relevant reference files

---

## Mode 3: Full Audit

Systematically review each skill component:

### Architecture Check
```bash
# Get current directory structure
find src -type d -maxdepth 2
# Check for new top-level patterns
ls -la src/
```
Compare to `reference/architecture.md`

### Data Flows Check
```bash
# Find API routes
find src -path "*/api/*" -name "*.ts"
# Find key service files
find src -name "*service*" -o -name "*Service*"
```
Compare to `reference/data-flows.md`

### Error Patterns Check
```bash
# Find error classes/types
grep -r "class.*Error" --include="*.ts" src/
grep -r "throw new" --include="*.ts" src/
```
Compare to `reference/error-patterns.md`

### Commands Check
```bash
# Check package.json scripts
cat package.json | grep -A 50 '"scripts"'
```
Compare to commands table in SKILL.md

Generate report of what's outdated.

---

## Mode 4: Error Pattern Capture

Ask the user:
1. What error did you encounter? (exact message)
2. What was the root cause?
3. How did you fix it?

Then append to `reference/error-patterns.md`:

```markdown
---

## [Error Category]

### Error: [ErrorName]

**Symptom**:
```
[exact error message]
```

**Root Cause**:
[explanation]

**Investigation**:
```bash
[commands to diagnose]
```

**Solution**:
[fix description]

**Prevention**:
- [how to avoid in future]
```

---

## Output Format

After analysis, provide:

1. **Summary**: What changed / what's stale
2. **Proposed Updates**: Specific patches with file paths
3. **Verification**: How to confirm updates are accurate

Ask user to confirm before making changes.

---

User's request: $ARGUMENTS
