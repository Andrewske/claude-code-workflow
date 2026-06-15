# Email Management Deep Dive

## Gmail Search Operators

Use in `+triage --query '...'` or `--params '{"q":"..."}'`.

| Operator | Example | What it finds |
|----------|---------|---------------|
| `from:` | `from:linkedin.com` | Emails from LinkedIn |
| `to:` | `to:me` | Emails sent to you |
| `subject:` | `subject:invoice` | Subject contains "invoice" |
| `has:attachment` | `has:attachment` | Emails with attachments |
| `filename:` | `filename:pdf` | Attachments of that type |
| `larger:` | `larger:5M` | Emails over 5MB |
| `smaller:` | `smaller:100K` | Emails under 100KB |
| `older_than:` | `older_than:1y` | Older than 1 year |
| `newer_than:` | `newer_than:7d` | From the last 7 days |
| `before:` | `before:2025/01/01` | Before a specific date |
| `after:` | `after:2026/01/01` | After a specific date |
| `is:unread` | `is:unread` | Unread messages |
| `is:read` | `is:read` | Read messages |
| `is:starred` | `is:starred` | Starred messages |
| `in:inbox` | `in:inbox` | In inbox (not archived) |
| `in:trash` | `in:trash` | In trash |
| `in:anywhere` | `in:anywhere` | All mail including trash/spam |
| `category:` | `category:promotions` | Gmail category tab |
| `label:` | `label:finance` | Has specific label |
| `-` (NOT) | `-from:boss` | Exclude matches |
| `OR` | `from:a OR from:b` | Either condition |
| `()` | `(from:a OR from:b) subject:meeting` | Grouping |

### Common Search Recipes

```bash
# Large old emails eating storage
gws gmail +triage --query 'larger:10M older_than:6m' --max 20 --format table

# Newsletters and marketing
gws gmail +triage --query 'category:promotions older_than:1m' --max 50 --format table

# Social notifications
gws gmail +triage --query 'category:social older_than:1m' --max 50 --format table

# Unread older than 3 months (probably not important)
gws gmail +triage --query 'is:unread older_than:3m' --max 50 --format table

# Automated/noreply emails
gws gmail +triage --query 'from:noreply OR from:no-reply' --max 50 --format table

# Emails from a specific domain
gws gmail +triage --query 'from:@linkedin.com' --max 50 --format table
```

## Bulk Operations

### Collect Message IDs

All bulk operations need message IDs. Get them from list queries:

```bash
# Get IDs for a query
gws gmail users messages list --params '{"userId":"me","q":"from:noreply@example.com older_than:6m","maxResults":100}' --format json
```

Extract IDs from the JSON `messages[].id` array.

### Bulk Label

```bash
gws gmail users messages batchModify --params '{"userId":"me"}' \
  --json '{"ids":["id1","id2","id3"],"addLabelIds":["LABEL_ID"]}'
```

### Bulk Archive

```bash
gws gmail users messages batchModify --params '{"userId":"me"}' \
  --json '{"ids":["id1","id2","id3"],"removeLabelIds":["INBOX"]}'
```

### Bulk Trash (Recoverable)

Move to trash one at a time (no batch trash endpoint):

```bash
gws gmail users messages trash --params '{"userId":"me","id":"MSG_ID"}'
```

For many messages, loop through IDs.

### Bulk Permanent Delete

```bash
gws gmail users messages batchDelete --params '{"userId":"me"}' \
  --json '{"ids":["id1","id2","id3"]}'
```

**WARNING: This is permanent and cannot be undone.**

### Pagination for Large Cleanups

Gmail returns max 100-500 messages per request. For large cleanups:

```bash
# Page through all results
gws gmail users messages list \
  --params '{"userId":"me","q":"category:promotions older_than:1y","maxResults":500}' \
  --page-all --page-limit 5 --format json
```

## Filter Patterns

### Auto-Delete (Skip Inbox + Trash)

```bash
gws gmail users settings filters create --params '{"userId":"me"}' \
  --json '{
    "criteria": {"from": "newsletters@example.com"},
    "action": {"removeLabelIds": ["INBOX"], "addLabelIds": ["TRASH"]}
  }'
```

### Auto-Archive (Skip Inbox, Keep in All Mail)

```bash
gws gmail users settings filters create --params '{"userId":"me"}' \
  --json '{
    "criteria": {"from": "notifications@github.com"},
    "action": {"removeLabelIds": ["INBOX"]}
  }'
```

### Auto-Label + Skip Inbox

```bash
gws gmail users settings filters create --params '{"userId":"me"}' \
  --json '{
    "criteria": {"from": "receipts@amazon.com"},
    "action": {"removeLabelIds": ["INBOX"], "addLabelIds": ["LABEL_ID"]}
  }'
```

### Auto-Star Important Senders

```bash
gws gmail users settings filters create --params '{"userId":"me"}' \
  --json '{
    "criteria": {"from": "boss@company.com"},
    "action": {"addLabelIds": ["STARRED"]}
  }'
```

### Auto-Label by Subject Pattern

```bash
gws gmail users settings filters create --params '{"userId":"me"}' \
  --json '{
    "criteria": {"query": "subject:(receipt OR invoice OR order confirmation)"},
    "action": {"addLabelIds": ["LABEL_ID"]}
  }'
```

### List All Filters

```bash
gws gmail users settings filters list --params '{"userId":"me"}' --format table
```

### Delete a Filter

```bash
gws gmail users settings filters delete --params '{"userId":"me","id":"FILTER_ID"}'
```

## Label Management

### System Labels (Built-in)

These exist by default and can't be deleted:
- `INBOX`, `SENT`, `DRAFT`, `TRASH`, `SPAM`
- `STARRED`, `UNREAD`, `IMPORTANT`
- `CATEGORY_PERSONAL`, `CATEGORY_SOCIAL`, `CATEGORY_PROMOTIONS`, `CATEGORY_UPDATES`, `CATEGORY_FORUMS`

### Create Labels

```bash
# Simple label
gws gmail users labels create --params '{"userId":"me"}' \
  --json '{"name":"Receipts"}'

# Nested label
gws gmail users labels create --params '{"userId":"me"}' \
  --json '{"name":"Finance/Receipts"}'

# Hidden from message list (for automation)
gws gmail users labels create --params '{"userId":"me"}' \
  --json '{"name":"Auto-Processed","messageListVisibility":"hide","labelListVisibility":"labelShow"}'
```

### Update Label

```bash
gws gmail users labels patch --params '{"userId":"me","id":"LABEL_ID"}' \
  --json '{"name":"New Name"}'
```

### Delete Label

```bash
# Removes label from all messages and deletes it
gws gmail users labels delete --params '{"userId":"me","id":"LABEL_ID"}'
```

## Guided Cleanup Conversation Flow

When a user says they want to clean up their email, guide them through this flow:

### 1. Audit

Run these in sequence, summarize findings:
- Total unread count
- Promotional email count
- Social notification count
- Large emails (>5MB)
- Old unread (>3 months)

### 2. Quick Wins

Present the easiest wins first:
- "You have X promotional emails older than a month. Want to trash them?"
- "X emails from [sender] — want to unsubscribe and clean up?"
- "X large emails taking up storage — want to review?"

### 3. Organize

After cleanup, suggest organization:
- "Want labels for Receipts, Important, or other categories?"
- "Should we set up filters so [sender] auto-labels from now on?"

### 4. Automate

Set up filters so it stays clean:
- Auto-trash for senders they never read
- Auto-label for senders they want organized
- Auto-archive for low-priority notifications
