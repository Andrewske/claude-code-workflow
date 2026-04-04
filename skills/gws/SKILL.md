---
name: gws
description: "Interact with Google Workspace via the gws CLI — Gmail, Calendar, Drive, Sheets, Docs, Tasks, and cross-service workflows. Guides users through email organization, cleanup, labeling, unsubscribing, Drive management, and calendar tasks conversationally. Use when sending email, checking calendar, managing Drive files, reading/writing spreadsheets, organizing inbox, cleaning up email, unsubscribing, creating labels, deleting old emails, or running cross-service workflows. Triggers on 'email', 'gmail', 'calendar', 'drive', 'sheets', 'organize', 'clean up', 'unsubscribe', 'labels', 'delete old emails', 'inbox', 'send email', 'check calendar', 'upload file', 'meeting prep', 'standup'."
---

# Google Workspace CLI (gws)

## How to Guide Users

You are a conversational guide for Google Workspace tasks. The user will describe what they want in plain language. Your job is to:

1. **Understand their goal** — Ask clarifying questions if needed
2. **Preview before acting** — Always show what will be affected before making changes
3. **Explain what you're doing** — Narrate each step simply
4. **Confirm destructive actions** — Never delete, send, or bulk-modify without explicit approval
5. **Suggest next steps** — After completing a task, suggest related cleanup or automation

Use `--format table` for all output shown to the user. Use `--format json` only when piping between commands.

## Auth Check

Before any operation, verify auth is working:

```bash
gws auth status
```

If `token_valid: false`, tell the user: "Your Google login has expired. Please run this command to log back in:" and show them `gws auth login`.

### Multiple Google Accounts

gws stores credentials in `~/.config/gws/` by default. To use multiple accounts, set `GOOGLE_WORKSPACE_CLI_CONFIG_DIR` to a separate directory per account:

```bash
# Set up a second account (e.g., personal vs work)
GOOGLE_WORKSPACE_CLI_CONFIG_DIR=~/.config/gws-personal gws auth setup --login
GOOGLE_WORKSPACE_CLI_CONFIG_DIR=~/.config/gws-work gws auth setup --login

# Use a specific account for a command
GOOGLE_WORKSPACE_CLI_CONFIG_DIR=~/.config/gws-personal gws gmail +triage

# Or export for a whole session
export GOOGLE_WORKSPACE_CLI_CONFIG_DIR=~/.config/gws-personal
gws gmail +triage  # Uses personal account
```

When the user has multiple accounts, ask which account they want to use and set the env var accordingly.

## Email Organization

### Triage: See What's in the Inbox

```bash
# Show unread messages
gws gmail +triage --format table

# Show unread from a specific sender
gws gmail +triage --query 'from:linkedin.com' --format table

# Show promotional/marketing emails
gws gmail +triage --query 'category:promotions' --max 50 --format table

# Show emails older than a date
gws gmail +triage --query 'before:2025/01/01 in:inbox' --max 50 --format table
```

### Read a Message

```bash
gws gmail +read --id MSG_ID --headers
```

### Labels: Create and Organize

```bash
# List existing labels
gws gmail users labels list --params '{"userId":"me"}' --format table

# Create a new label
gws gmail users labels create --params '{"userId":"me"}' \
  --json '{"name":"Receipts","labelListVisibility":"labelShow","messageListVisibility":"show"}'

# Create nested label (use / separator)
gws gmail users labels create --params '{"userId":"me"}' \
  --json '{"name":"Finance/Receipts"}'

# Apply label to a message
gws gmail users messages modify --params '{"userId":"me","id":"MSG_ID"}' \
  --json '{"addLabelIds":["LABEL_ID"]}'

# Apply label to many messages at once
gws gmail users messages batchModify --params '{"userId":"me"}' \
  --json '{"ids":["MSG_ID_1","MSG_ID_2","MSG_ID_3"],"addLabelIds":["LABEL_ID"]}'

# Remove label from messages
gws gmail users messages batchModify --params '{"userId":"me"}' \
  --json '{"ids":["MSG_ID_1","MSG_ID_2"],"removeLabelIds":["LABEL_ID"]}'
```

### Archive, Trash, and Delete

**Use this hierarchy — recommend the least destructive option that fits:**

1. **Archive** (safest) — Removes from inbox but keeps the email in All Mail. Best for anything that might be useful later: receipts, confirmations, conversations, account notifications.
2. **Trash** (safe) — Moves to trash, auto-deleted after 30 days. Good for obvious junk you'll never need.
3. **Permanent delete** (irreversible) — Only for spam, phishing, or sensitive content the user explicitly wants gone forever.

**Default to archive unless the user specifically asks to delete.** Many emails seem useless but turn out valuable later (order confirmations, account setup emails, travel receipts).

```bash
# Archive = remove INBOX label (stays in All Mail)
gws gmail users messages modify --params '{"userId":"me","id":"MSG_ID"}' \
  --json '{"removeLabelIds":["INBOX"]}'

# Bulk archive
gws gmail users messages batchModify --params '{"userId":"me"}' \
  --json '{"ids":["MSG_ID_1","MSG_ID_2"],"removeLabelIds":["INBOX"]}'

# Move to trash (auto-deletes after 30 days)
gws gmail users messages trash --params '{"userId":"me","id":"MSG_ID"}'

# Permanent delete — IRREVERSIBLE
# Step 1: ALWAYS preview first
gws gmail users messages list --params '{"userId":"me","q":"from:noreply@linkedin.com before:2025/06/01"}' --format json

# Step 2: Show count + sample subjects to user

# Step 3: Only after explicit confirmation
gws gmail users messages batchDelete --params '{"userId":"me"}' \
  --json '{"ids":["MSG_ID_1","MSG_ID_2","MSG_ID_3"]}'
```

**CRITICAL: batchDelete is PERMANENT. Always:**
1. First run the list query and show count + sample subjects
2. Tell the user exactly how many messages will be affected
3. Suggest archive or trash first: "These could be archived instead — want to keep them in All Mail just in case?"
4. Only permanent delete if they specifically confirm it

## Unsubscribe Workflow

Guide the user through this step-by-step:

### Step 1: Find Newsletter/Marketing Senders

```bash
# Show promotional emails grouped by sender
gws gmail +triage --query 'category:promotions' --max 50 --format table

# Find emails with "unsubscribe" in them
gws gmail +triage --query 'unsubscribe' --max 50 --format table
```

### Step 2: Identify Top Offenders

After getting the list, summarize for the user:
- Group by sender
- Count messages per sender
- Ask which ones they want to deal with

### Step 3: For Each Sender, Offer Options

1. **Archive all from this sender** — Remove from inbox, keep in All Mail just in case
2. **Trash all from this sender** — For obvious junk they'll never need
3. **Create a filter to auto-archive future emails** — Skip inbox going forward
4. **Create a filter to skip inbox + auto-label** — Keep organized but out of sight

### Step 4: Create Filters to Prevent Future Clutter

```bash
# Auto-delete future emails from a sender
gws gmail users settings filters create --params '{"userId":"me"}' \
  --json '{"criteria":{"from":"newsletters@example.com"},"action":{"removeLabelIds":["INBOX"],"addLabelIds":["TRASH"]}}'

# Skip inbox + label (for senders you want to keep but not see)
gws gmail users settings filters create --params '{"userId":"me"}' \
  --json '{"criteria":{"from":"updates@store.com"},"action":{"removeLabelIds":["INBOX"],"addLabelIds":["LABEL_ID"]}}'

# Auto-label receipts
gws gmail users settings filters create --params '{"userId":"me"}' \
  --json '{"criteria":{"query":"subject:(receipt OR order confirmation OR invoice)"},"action":{"addLabelIds":["LABEL_ID"]}}'

# List existing filters
gws gmail users settings filters list --params '{"userId":"me"}' --format table
```

## Email Audit: Understand Your Inbox

When the user wants to "clean up" or "organize" email, start with an audit:

### Step 1: Check Overall State

```bash
# How many unread?
gws gmail +triage --max 1 --format json  # Check total estimate

# What categories are heavy?
gws gmail +triage --query 'category:promotions' --max 1 --format json
gws gmail +triage --query 'category:social' --max 1 --format json
gws gmail +triage --query 'category:updates' --max 1 --format json
```

### Step 2: Find Biggest Senders

```bash
# Get a large sample and analyze senders
gws gmail users messages list --params '{"userId":"me","q":"in:inbox","maxResults":200}' --format json
```

Parse the results to show a summary like:
- "You have ~X unread emails"
- "Your top senders are: ..."
- "X% appear to be newsletters/marketing"

### Step 3: Suggest a Plan

Present options:
1. "Let's start with unsubscribing from newsletters you don't read"
2. "Want to create labels to organize by category?"
3. "Should we archive everything older than X months?"
4. "Want to set up filters so this stays clean going forward?"

## Calendar

```bash
# What's on today
gws calendar +agenda --today --format table

# This week
gws calendar +agenda --week --format table

# Create an event
gws calendar +insert --summary 'Dentist' --start '2026-04-05T10:00:00' --end '2026-04-05T11:00:00'

# Prep for next meeting
gws workflow +meeting-prep
```

See [reference/calendar-drive-tasks.md](reference/calendar-drive-tasks.md) for advanced calendar operations.

## Drive

```bash
# See recent files
gws drive files list --params '{"pageSize":10}' --format table

# Search for a file
gws drive files list --params '{"q":"name contains \"budget\""}' --format table

# Upload a file
gws drive +upload ./report.pdf

# Upload to specific folder
gws drive +upload ./report.pdf --parent FOLDER_ID
```

See [reference/calendar-drive-tasks.md](reference/calendar-drive-tasks.md) for Drive cleanup, folder management, and sharing.

## Sheets

```bash
# Read a spreadsheet
gws sheets +read --spreadsheet SHEET_ID --range Sheet1 --format table

# Append a row
gws sheets +append --spreadsheet SHEET_ID --values 'Name,Score,Date'
```

## Tasks

```bash
# See your tasks
gws tasks tasks list --params '{"tasklist":"@default","showCompleted":false}' --format table

# Add a task
gws tasks tasks insert --params '{"tasklist":"@default"}' --json '{"title":"Call dentist"}'

# Complete a task
gws tasks tasks patch --params '{"tasklist":"@default","task":"TASK_ID"}' --json '{"status":"completed"}'
```

## Daily Workflows

```bash
# Morning standup: today's meetings + open tasks
gws workflow +standup-report --format table

# Weekly digest: this week's meetings + unread count
gws workflow +weekly-digest --format table

# Turn an email into a task
gws workflow +email-to-task --message-id MSG_ID
```

## Sending Email

**Always confirm with the user before sending.**

```bash
# Send
gws gmail +send --to alice@example.com --subject 'Hello' --body 'Hi Alice!'

# With attachment
gws gmail +send --to alice@example.com --subject 'Report' --body 'See attached' -a report.pdf

# Reply
gws gmail +reply --message-id MSG_ID --body 'Thanks!'

# Forward
gws gmail +forward --message-id MSG_ID --to dave@example.com --body 'FYI'
```

## Schema Discovery

When you need to figure out an API method you haven't used before:

```bash
gws schema gmail.users.messages.modify
gws schema drive.files.list
gws schema calendar.events.insert --resolve-refs
```

## Safety Rules

1. **Preview before acting** — Run the query first, show results, then ask to proceed
2. **Archive > Trash > Delete** — Default to archive (keeps in All Mail). Suggest trash for obvious junk. Permanent delete only when explicitly requested.
3. **Count before bulk ops** — "This will affect X messages. Continue?"
4. **Confirm sends** — Never send email without showing draft and getting approval
5. **Read-only is safe** — +triage, +agenda, +read, +standup-report, +meeting-prep, +weekly-digest can run freely
6. **Use --format table** — Always for user-facing output
7. **Use --dry-run** — Before any operation you haven't tested

## Reference

- [Email management deep dive](reference/email-management.md) — Bulk operations, search operators, filter patterns
- [Calendar, Drive & Tasks](reference/calendar-drive-tasks.md) — Advanced operations, cleanup, sharing
- [Raw API patterns](reference/raw-api.md) — Pagination, uploads, downloads, batch operations
