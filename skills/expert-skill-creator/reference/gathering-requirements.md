# Gathering Requirements

Questions to ask before building a skill.

## For All Skills

### Core Questions
1. **What problem does this solve?**
   - What task is difficult or repetitive without this skill?
   - What context do you keep providing manually?

2. **What are the trigger scenarios?**
   - What would a user say that should activate this skill?
   - What file types are involved?
   - What action words are relevant?

3. **What does Claude not know?**
   - What domain-specific knowledge is needed?
   - What procedures are non-obvious?
   - What conventions are project-specific?

4. **What should the output look like?**
   - Are there format requirements?
   - Are there quality standards?
   - Are there validation criteria?

### Scope Questions
5. **What's in scope?**
   - List specific capabilities

6. **What's explicitly out of scope?**
   - What should this skill NOT try to do?
   - What should trigger a different skill?

---

## For Generic/Utility Skills

### Capability Questions
1. **What formats/inputs are supported?**
   - File types
   - Data formats
   - Input sources

2. **What operations are needed?**
   - Create, read, update, delete?
   - Transform, convert, validate?
   - Extract, merge, split?

3. **Are there common variations?**
   - Different modes or options
   - Platform differences
   - Configuration parameters

### Implementation Questions
4. **Is deterministic reliability needed?**
   - Should this be a script vs. instructions?
   - Is validation required?

5. **What libraries/tools are best?**
   - What's the canonical approach?
   - What are the dependencies?

6. **What errors can occur?**
   - Common failure modes
   - How to recover

---

## For Domain Knowledge Skills

### Data Questions
1. **What data sources exist?**
   - Databases, APIs, files
   - Table names, schemas
   - Access patterns

2. **What are the key entities?**
   - Main objects/concepts
   - Relationships between them
   - Naming conventions

3. **What queries are common?**
   - Frequent lookups
   - Standard reports
   - Common filters

### Business Logic Questions
4. **What rules apply to the data?**
   - Filtering rules (e.g., exclude test data)
   - Calculation methods
   - Data quality constraints

5. **What terms mean what?**
   - Domain-specific vocabulary
   - Acronyms and abbreviations
   - Metrics definitions

6. **Who owns what?**
   - Data ownership
   - Access permissions
   - Approval workflows

---

## For Project Knowledge Skills

### Architecture Questions
1. **What's the tech stack?**
   - Frontend framework
   - Backend/API layer
   - Database
   - External services

2. **What are the main components?**
   - Draw a simple diagram
   - How do they connect?
   - What are the boundaries?

3. **Where does code live?**
   - Directory structure
   - Key file locations
   - Naming conventions

### Flow Questions
4. **What are the main user flows?**
   - User does X → starts at file Y
   - Data flows from A → B → C

5. **What are the entry points?**
   - API routes
   - UI components
   - Background jobs

6. **How does data flow?**
   - Request path
   - Data transformations
   - Storage locations

### Debugging Questions
7. **What are common bugs?**
   - Error messages you see often
   - Root causes
   - How they were fixed

8. **What debugging steps work?**
   - How do you investigate issues?
   - What logs are useful?
   - What tools help?

9. **What are the gotchas?**
   - Non-obvious behaviors
   - Common mistakes
   - Historical decisions

### Operations Questions
10. **What commands are essential?**
    - Start/stop services
    - Run tests
    - Deploy

11. **What environment setup is needed?**
    - Environment variables
    - Config files
    - Dependencies

12. **What monitoring exists?**
    - Logs location
    - Health checks
    - Metrics

---

## For Complex Workflow Skills

### Process Questions
1. **What are the steps?**
   - Linear or branching?
   - Required order
   - Optional steps

2. **What validation is needed?**
   - Between which steps?
   - What constitutes valid?
   - How to recover from invalid?

3. **What are the decision points?**
   - When to branch?
   - What determines the path?

### Reliability Questions
4. **What can go wrong?**
   - Each step's failure modes
   - Recovery procedures

5. **What needs to be atomic?**
   - All-or-nothing operations
   - Rollback requirements

6. **What's the happy path vs. edge cases?**
   - Common flow
   - Exceptions

---

## Question Prioritization

### Must Ask (Blocking)
- What's the trigger scenario?
- What does Claude not know?
- What's the expected output?

### Should Ask (Important)
- What errors can occur?
- What validation is needed?
- What's out of scope?

### Could Ask (Nice to Have)
- What variations exist?
- What's the history/context?
- Who else might use this?

---

## Sample Conversation Flow

### Opening
> "I'd like to help you create a skill. To make sure it's effective, I have a few questions.
> 
> First, what problem are you trying to solve? What task would this skill help with?"

### Follow-up Based on Type
**If utility skill:**
> "What file types or inputs will this work with? And what are the main operations—creating, converting, extracting?"

**If domain skill:**
> "What data sources are involved? And what queries or lookups are most common?"

**If project skill:**
> "Can you describe the tech stack briefly? And what are the most common bugs or issues you debug?"

### Closing
> "Based on what you've shared, I'll create a [type] skill. Before I start, is there anything else Claude should know that isn't obvious from the codebase?"
